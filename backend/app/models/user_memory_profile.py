from uuid import uuid4
from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, JSON, func, Index, UniqueConstraint
from sqlalchemy.orm import relationship
from .base import Base

# pgvector support (T009 data-model + migration uses ARRAY fallback)
try:
    from pgvector.sqlalchemy import Vector
    _VECTOR_TYPE = Vector(1536)
except ImportError:
    _VECTOR_TYPE = None  # fallback; migration will use proper Vector too; dev without pkg uses JSON


class UserMemoryProfile(Base):
    """user_memory_profiles model exactly per data-model.md (T009).

    1:1 with user (unique user_id). Stores tone/ICP/cadence for injection into LLM (T007+).
    profile_embedding vector for future semantic recall.
    Prepares T006/T013 personalization + memory profile editor.
    """

    __tablename__ = "user_memory_profiles"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, unique=True, index=True)
    tone_samples = Column(JSON, nullable=True)  # array of {opener, outcome, accepted_at}
    icp_industries = Column(JSON, nullable=True)  # array<string>
    typical_cadence = Column(JSON, nullable=True)  # e.g. [4, 9, 14]
    profile_embedding = Column(_VECTOR_TYPE if _VECTOR_TYPE else JSON, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationship
    user = relationship("User", back_populates="memory_profile")

    __table_args__ = (
        UniqueConstraint("user_id", name="uq_user_memory_profile"),
        Index("ix_user_memory_profiles_user_created", "user_id", "created_at"),
    )