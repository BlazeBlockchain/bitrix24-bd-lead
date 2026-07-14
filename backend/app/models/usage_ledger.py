from uuid import uuid4
from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, Integer, func, Index
from sqlalchemy.orm import relationship
from .base import Base


class UsageLedger(Base):
    """usage_ledger per data-model.md exactly.

    For billing + cost guardrails (T007/T009).
    - id UUID
    - user_id FK
    - lead_id nullable FK
    - model str
    - input_tokens, output_tokens, estimated_cost_cents
    - created_at
    """

    __tablename__ = "usage_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    lead_id = Column(UUID(as_uuid=True), ForeignKey("leads.id"), nullable=True, index=True)
    model = Column(String(100), nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    estimated_cost_cents = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="usage_ledger")
    # lead = relationship("Lead", back_populates=...)  # optional

    __table_args__ = (
        Index("ix_usage_ledger_user_created", "user_id", "created_at"),
    )
