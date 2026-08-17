from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..config import get_settings
from ..database import get_db
from ..models import AuditLog, KnowledgeItem, Patient, User
from ..schemas import (
    AuditOut,
    KnowledgeCreate,
    KnowledgeItemOut,
    SystemStatusOut,
)
from ..security import require_roles
from ..services.embeddings import get_embedder
from ..services.audit import write_audit
from ..services.pgvector_store import sync_knowledge_embeddings

router = APIRouter(prefix="/api/admin", tags=["admin"])

admin_dependency = require_roles("admin")


@router.get("/knowledge", response_model=list[KnowledgeItemOut])
def list_knowledge(
    db: Session = Depends(get_db),
    user: User = Depends(admin_dependency),
):
    return db.query(KnowledgeItem).order_by(KnowledgeItem.id).all()


@router.post("/knowledge", response_model=KnowledgeItemOut)
def create_knowledge(
    payload: KnowledgeCreate,
    db: Session = Depends(get_db),
    user: User = Depends(admin_dependency),
):
    item = KnowledgeItem(
        title=payload.title,
        category=payload.category,
        content=payload.content,
        source=payload.source or "管理员录入",
        tags=payload.tags,
    )
    item.embedding = get_embedder().embed(
        f"{item.title} {item.category} {item.content} {' '.join(payload.tags)}"
    )
    db.add(item)
    write_audit(
        db,
        actor=user.username,
        action="knowledge_create",
        target_type="knowledge",
        target_id=item.id,
        detail={"title": item.title},
    )
    db.commit()
    sync_knowledge_embeddings(db)
    db.refresh(item)
    return item


@router.delete("/knowledge/{item_id}")
def delete_knowledge(
    item_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(admin_dependency),
):
    item = db.get(KnowledgeItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="知识条目不存在")
    write_audit(
        db,
        actor=user.username,
        action="knowledge_delete",
        target_type="knowledge",
        target_id=item.id,
        detail={"title": item.title},
    )
    db.delete(item)
    db.commit()
    return {"ok": True}


@router.get("/audit", response_model=list[AuditOut])
def list_audit(
    db: Session = Depends(get_db),
    user: User = Depends(admin_dependency),
):
    logs = db.query(AuditLog).order_by(AuditLog.id.desc()).limit(100).all()
    return [AuditOut.model_validate(item) for item in logs]


@router.get("/system", response_model=SystemStatusOut)
def system_status(
    db: Session = Depends(get_db),
    user: User = Depends(admin_dependency),
):
    settings = get_settings()
    anthropic = "anthropic" in settings.llm_base_url or settings.llm_style == "anthropic"
    return SystemStatusOut(
        provider_mode=(
            "anthropic"
            if settings.llm_api_key and anthropic
            else "openai_compatible"
            if settings.llm_api_key
            else "mock"
        ),
        model_name=settings.llm_model,
        database_url=settings.database_url,
        api_base_url=settings.llm_base_url,
        knowledge_count=db.query(KnowledgeItem).count(),
        patient_count=db.query(Patient).count(),
    )
