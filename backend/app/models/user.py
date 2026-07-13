from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UUID, func
from sqlalchemy.orm import relationship
from .base import Base


class User(Base):
    """Stub User model per data-model.md (T004 skeleton; expand in T005/T009)."""

    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email = Column(String(255), unique=True, nullable=False, index=True)
    google_sub = Column(String(255), nullable=True)
    display_name = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=func.now(), nullable=False)
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)

    # Relationships (stubs)
    # leads = relationship(...)
    # crm_connections = relationship(...)

    __table_args__ = (
        # Add indexes as needed
    )
