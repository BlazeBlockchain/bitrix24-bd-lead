from uuid import uuid4
from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, Text, func, JSON, Index
from sqlalchemy.orm import relationship
from .base import Base


class Lead(Base):
    """Lead model per data-model.md exactly.

    - id UUID PK
    - user_id FK
    - company_name, contact_name, contact_role, signal, signal_type, pain_point, notes
    - email, linkedin_url nullable
    - enriched: JSON (snapshot, opener, tasks[{title,description,due_in_days,rationale}])
    - crm_provider, crm_contact_id, crm_deal_id
    - created_at
    """

    __tablename__ = "leads"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    company_name = Column(String(255), nullable=False)
    contact_name = Column(String(255), nullable=False)
    contact_role = Column(String(255), nullable=False)
    signal = Column(Text, nullable=True)
    signal_type = Column(String(50), nullable=True)
    pain_point = Column(Text, nullable=True)
    notes = Column(Text, nullable=True)
    email = Column(String(255), nullable=True)
    linkedin_url = Column(String(255), nullable=True)
    enriched = Column(JSON, nullable=True)  # snapshot, opener, tasks + rationale from T007
    crm_provider = Column(String(50), nullable=True)
    crm_contact_id = Column(String(255), nullable=True)
    crm_deal_id = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationships
    user = relationship("User", back_populates="leads")
    outreach_history = relationship("OutreachHistory", back_populates="lead", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_leads_user_created", "user_id", "created_at"),  # heavy per data-model for history queries
    )
