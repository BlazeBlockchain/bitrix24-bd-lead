"""Backend services (T008+).

Currently: lead orchestration (centralized CrmClient flow).
Prepares for T007 LLM, T009 models, etc.
"""
from .lead_service import create_lead_with_followups, _add_days  # type: ignore[attr-defined]

__all__ = ["create_lead_with_followups"]
