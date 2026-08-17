from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .database import Base, SessionLocal, engine, ensure_sqlite_schema
from .routers import admin, auth, departments, ops, patients, triage
from .seed import seed
from .services.embeddings import ensure_knowledge_embeddings
from .services.pgvector_store import ensure_pgvector

settings = get_settings()
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_: FastAPI):
    Base.metadata.create_all(bind=engine)
    ensure_sqlite_schema()
    ensure_pgvector()
    with SessionLocal() as db:
        seed(db)
        ensure_knowledge_embeddings(db)
    yield


app = FastAPI(
    title=settings.app_name,
    description="AI 智慧医院平台 API：智能分诊、AI 病历助手、运营预警。",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(departments.router)
app.include_router(triage.router)
app.include_router(patients.router)
app.include_router(ops.router)
app.include_router(admin.router)


@app.get("/api/health")
def health():
    return {"status": "ok", "app": settings.app_name}


if FRONTEND_DIST.exists():
    app.mount(
        "/",
        StaticFiles(directory=FRONTEND_DIST, html=True),
        name="frontend",
    )
