from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, DateTime, UUID, ForeignKey, JSON, UniqueConstraint, func
from .base import Base


class CrmConnection(Base):
    """Stub CrmConnection model per data-model.md.

    encrypted_credentials will hold envelope-encrypted tokens (T006).
    For T004 skeleton, auth is stubbed via top-level config tokens.
    """

    __tablename__ = "crm_connections"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False, index=True)
    provider = Column(String(50), nullable=False)  # 'bitrix24' | 'hubspot'
    auth_type = Column(String(20), nullable=False, default="webhook")  # 'webhook' | 'oauth'
    encrypted_credentials = Column(String, nullable=True)  # placeholder; bytea/JSON later
    scopes = Column(JSON, nullable=True)
    expires_at = Column(DateTime, nullable=True)
    last_validated_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now(), nullable=False)

    __table_args__ = (
        UniqueConstraint("user_id", "provider", name="uq_user_provider"),
    )
