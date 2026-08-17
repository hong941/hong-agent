from datetime import datetime, timezone

from sqlalchemy import JSON, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from .database import Base


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Department(Base):
    __tablename__ = "departments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), unique=True, nullable=False, index=True)
    code = Column(String(40), unique=True, nullable=False)
    description = Column(Text, default="")
    avg_wait_minutes = Column(Integer, default=20)
    load = Column(Integer, default=30)
    capacity = Column(Integer, default=100)

    patients = relationship("Patient", back_populates="department")
    doctors = relationship("User", back_populates="department")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(80), unique=True, nullable=False, index=True)
    hashed_password = Column(String(256), nullable=False)
    name = Column(String(80), nullable=False)
    role = Column(String(20), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)

    department = relationship("Department", back_populates="doctors")


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(80), nullable=False)
    age = Column(Integer, nullable=False)
    gender = Column(String(10), default="未知")
    phone = Column(String(30), default="")
    chief_complaint = Column(Text, default="")
    symptoms = Column(JSON, default=list)
    allergies = Column(Text, default="")
    medications = Column(Text, default="")
    medical_history = Column(Text, default="")
    risk_level = Column(String(20), default="green", index=True)
    risk_score = Column(Float, default=0)
    triage_reason = Column(Text, default="")
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=True)
    status = Column(String(30), default="triage", index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    department = relationship("Department", back_populates="patients")
    conversation = relationship(
        "TriageConversation", back_populates="patient", uselist=False
    )
    appointments = relationship(
        "Appointment", back_populates="patient", cascade="all, delete-orphan"
    )


class TriageConversation(Base):
    __tablename__ = "triage_conversations"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(
        Integer, ForeignKey("patients.id"), nullable=False, unique=True, index=True
    )
    messages = Column(JSON, default=list)
    completed = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), default=utcnow)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    patient = relationship("Patient", back_populates="conversation")


class Appointment(Base):
    __tablename__ = "appointments"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(
        Integer, ForeignKey("patients.id"), nullable=False, index=True
    )
    doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    department_id = Column(Integer, ForeignKey("departments.id"), nullable=False)
    scheduled_time = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(30), default="booked", index=True)
    notes = Column(Text, default="")
    created_at = Column(DateTime(timezone=True), default=utcnow)

    patient = relationship("Patient", back_populates="appointments")
    doctor = relationship("User")
    department = relationship("Department")


class KnowledgeItem(Base):
    __tablename__ = "knowledge_items"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    category = Column(String(80), nullable=False, index=True)
    content = Column(Text, nullable=False)
    source = Column(String(200), default="")
    tags = Column(JSON, default=list)
    embedding = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    actor = Column(String(80), nullable=False)
    action = Column(String(80), nullable=False, index=True)
    target_type = Column(String(40), default="")
    target_id = Column(Integer, nullable=True)
    detail = Column(JSON, default=dict)
    created_at = Column(DateTime(timezone=True), default=utcnow)
