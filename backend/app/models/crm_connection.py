from uuid import uuid4
from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, JSON, UniqueConstraint, func
from sqlalchemy.orm import relationship
from .base import Base


class CrmConnection(Base):
    """CrmConnection model exactly per data-model.md (T009).

    encrypted_credentials holds envelope-encrypted tokens (services/token_vault.py).
    (data-model bytea/JSON; kept as str for decrypt compat in vault).
    UNIQUE(user_id, provider). Integrates with current_user for T006 vault resolve.
    Prepares T010 API + T012 connections.
    """

    __tablename__ = "crm_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # 'bitrix24' | 'hubspot'
    auth_type = Column(String(20), nullable=False, default="webhook")  # 'webhook' | 'oauth'
    encrypted_credentials = Column(String, nullable=True)
    scopes = Column(JSON, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    last_validated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    # Relationship (T009)
    user = relationship("User", back_populates="crm_connections")

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )
