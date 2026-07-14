from uuid import uuid4
from sqlalchemy import Column, String, DateTime, UUID, func
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    """User model exactly per data-model.md (T009).

    1:1 memory profile, 1:N leads/crm_connections/outreach/usage.
    Heavy indexes on user_id+created_at for history/memory queries (added in models + migration).
    """

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    google_sub = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships (T009 full)
    leads = relationship("Lead", back_populates="user", cascade="all, delete-orphan")
    crm_connections = relationship("CrmConnection", back_populates="user", cascade="all, delete-orphan")
    memory_profile = relationship("UserMemoryProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    outreach_history = relationship("OutreachHistory", back_populates="user", cascade="all, delete-orphan")
    usage_ledger = relationship("UsageLedger", back_populates="user", cascade="all, delete-orphan")

    __table_args__ = (
        # Additional indexes per data-model (user_id+created_at heavy for queries)
    )
