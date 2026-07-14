"""
T026: Unit tests for CRM factory (provider selection).

Tests create_crm_client factory function:
- Provider selection (bitrix24 vs hubspot)
- Default provider (bitrix24)
- Token resolution (explicit config vs vault override)
- Correct adapter instantiation

All tests are hermetic (no real network or vault calls).
"""

import pytest
from unittest.mock import patch, MagicMock

from app.adapters.crm import create_crm_client
from app.adapters.crm.bitrix24 import Bitrix24Client
from app.adapters.crm.hubspot import HubspotClient


@pytest.mark.factory
class TestCrmFactory:
    """Tests for create_crm_client factory."""

    def test_default_provider_is_bitrix24(self):
        """Test that default provider is Bitrix24 (back-compat)."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.BITRIX24_WEBHOOK_URL = "https://test.bitrix24.com/rest/1/token/"

            client = create_crm_client()

            assert isinstance(client, Bitrix24Client)

    def test_explicit_bitrix24_provider(self):
        """Test explicit Bitrix24 provider selection."""
        webhook_url = "https://test.bitrix24.com/rest/1/test-token/"

        client = create_crm_client(provider="bitrix24", config=webhook_url)

        assert isinstance(client, Bitrix24Client)

    def test_explicit_hubspot_provider(self):
        """Test explicit HubSpot provider selection."""
        token = "pat-na1-test-token"

        client = create_crm_client(provider="hubspot", config=token)

        assert isinstance(client, HubspotClient)

    def test_config_passed_directly(self):
        """Test that explicit config is used directly (no vault lookup)."""
        webhook = "https://custom.bitrix24.com/rest/1/custom-token/"

        client = create_crm_client(provider="bitrix24", config=webhook)

        assert isinstance(client, Bitrix24Client)
        # Client should be initialized with the exact webhook URL
        assert client.base_url == webhook.rstrip("/")

    def test_config_fallback_to_settings_bitrix24(self):
        """Test fallback to settings for Bitrix24."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.BITRIX24_WEBHOOK_URL = "https://settings.bitrix24.com/rest/1/token/"

            client = create_crm_client(provider="bitrix24", config="")

            assert isinstance(client, Bitrix24Client)

    def test_config_fallback_to_settings_hubspot(self):
        """Test fallback to settings for HubSpot."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.HUBSPOT_ACCESS_TOKEN = "pat-na1-settings-token"

            client = create_crm_client(provider="hubspot", config="")

            assert isinstance(client, HubspotClient)

    def test_vault_resolution_when_current_user_provided(self):
        """Test vault resolution when current_user is provided."""
        mock_user = {"id": "user-123", "email": "test@example.com"}

        with patch("app.services.token_vault.resolve_token") as mock_vault:
            mock_vault.return_value = "vault-resolved-token"

            client = create_crm_client(
                provider="bitrix24",
                config="",
                current_user=mock_user,
            )

            # Vault should have been called
            mock_vault.assert_called_once_with(mock_user, "bitrix24")
            assert isinstance(client, Bitrix24Client)

    def test_vault_failure_raises_error(self):
        """Test that vault failure raises (no silent settings fallback)."""
        mock_user = {"id": "user-456"}

        with patch("app.services.token_vault.resolve_token") as mock_vault:
            mock_vault.side_effect = ValueError("Vault error (fail-closed)")

            import pytest as _pytest
            with _pytest.raises(ValueError, match="Vault error"):
                create_crm_client(
                    provider="bitrix24",
                    config="",
                    current_user=mock_user,
                )

    def test_explicit_config_overrides_vault(self):
        """Test that explicit config takes precedence over vault."""
        mock_user = {"id": "user-789"}
        explicit_token = "explicit-token-direct"

        with patch("app.services.token_vault.resolve_token") as mock_vault:
            client = create_crm_client(
                provider="hubspot",
                config=explicit_token,
                current_user=mock_user,
            )

            # Vault should NOT be called when config is explicit
            mock_vault.assert_not_called()
            assert isinstance(client, HubspotClient)

    def test_provider_case_insensitive_fallback(self):
        """Test that non-bitrix24/hubspot providers default to bitrix24."""
        with patch("app.config.settings") as mock_settings:
            mock_settings.BITRIX24_WEBHOOK_URL = "https://default.bitrix24.com/rest/1/token/"

            # Typo or unknown provider should fallback to bitrix24
            client = create_crm_client(provider="unknown_crm", config="")

            assert isinstance(client, Bitrix24Client)


@pytest.mark.factory
class TestCrmFactoryIntegration:
    """Integration tests for factory with multiple calls."""

    def test_multiple_provider_instances_independent(self):
        """Test that multiple client instances are independent."""
        bitrix_url = "https://bitrix.test.com/rest/1/token1/"
        hubspot_token = "pat-token-123"

        bitrix_client = create_crm_client(provider="bitrix24", config=bitrix_url)
        hubspot_client = create_crm_client(provider="hubspot", config=hubspot_token)

        assert isinstance(bitrix_client, Bitrix24Client)
        assert isinstance(hubspot_client, HubspotClient)
        # They should be different instances
        assert bitrix_client is not hubspot_client

    def test_same_provider_same_config_creates_new_instances(self):
        """Test that factory creates new instances (not cached)."""
        token = "pat-token-abc"

        client1 = create_crm_client(provider="hubspot", config=token)
        client2 = create_crm_client(provider="hubspot", config=token)

        # Should be different instances
        assert client1 is not client2
        # But same type
        assert type(client1) is type(client2)
