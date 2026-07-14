from uuid import uuid4
from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, Text, JSON, func, Index
from sqlalchemy.orm import relationship
from .base import Base

try:
    from pgvector.sqlalchemy import Vector
    _VECTOR_TYPE = Vector(1536)
except ImportError:
    _VECTOR_TYPE = None  # type: ignore


class OutreachHistory(Base):
    """outreach_history per data-model.md exactly.

    - id UUID
    - lead_id FK
    - user_id FK
    - action e.g. 'email_sent'
    - outcome nullable
    - notes text
    - embedding vector optional
    - created_at
    """

    __tablename__ = "outreach_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    action = Column(String(100), nullable=False)
    outcome = Column(String(100), nullable=True)
    notes = Column(Text, nullable=True)
    embedding = Column(_VECTOR_TYPE if _VECTOR_TYPE else JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    lead = relationship("Lead", back_populates="outreach_history")
    user = relationship("User", back_populates="outreach_history")

    __table_args__ = (
        Index("ix_outreach_history_user_created", "user_id", "created_at"),
    )
