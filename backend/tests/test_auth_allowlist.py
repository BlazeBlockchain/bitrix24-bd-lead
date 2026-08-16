"""Sign-in allowlist (AUTH_EMAIL_ALLOWLIST).

Covers the matcher directly. The endpoint gate in google_auth is a thin wrapper
around it: the parts of google_auth that are worth testing at the HTTP level all
sit behind a live Google token verification, which these tests deliberately do not
stand up. What matters here is that the default admits everyone (every other test
in the suite depends on that) and that a configured list is not trivially loose.
"""

import pytest

from app.api.auth import is_email_allowed
from app.config import settings


@pytest.fixture
def allowlist(monkeypatch):
    """Set AUTH_EMAIL_ALLOWLIST for one test."""
    def _set(value: str):
        monkeypatch.setattr(settings, "AUTH_EMAIL_ALLOWLIST", value)
    return _set


class TestDefaultIsOpen:
    def test_empty_allowlist_admits_anyone(self, allowlist):
        allowlist("")
        assert is_email_allowed("stranger@anywhere.test") is True

    def test_whitespace_only_allowlist_admits_anyone(self, allowlist):
        allowlist("   \n  ")
        assert is_email_allowed("stranger@anywhere.test") is True


class TestExactAddresses:
    def test_listed_address_is_admitted(self, allowlist):
        allowlist("rep@example.com")
        assert is_email_allowed("rep@example.com") is True

    def test_unlisted_address_is_refused(self, allowlist):
        allowlist("rep@example.com")
        assert is_email_allowed("someone-else@example.com") is False

    def test_matching_is_case_insensitive_on_both_sides(self, allowlist):
        allowlist("Rep@Example.COM")
        assert is_email_allowed("rEp@eXaMpLe.com") is True

    def test_entries_may_be_spaced_out(self, allowlist):
        allowlist(" a@example.com , b@example.com ")
        assert is_email_allowed("b@example.com") is True

    def test_empty_entries_are_skipped_not_treated_as_wildcards(self, allowlist):
        allowlist("a@example.com,,")
        assert is_email_allowed("stranger@anywhere.test") is False


class TestDomainRules:
    def test_domain_rule_admits_any_address_at_that_domain(self, allowlist):
        allowlist("@example.com")
        assert is_email_allowed("anyone@example.com") is True

    def test_domain_rule_refuses_other_domains(self, allowlist):
        allowlist("@example.com")
        assert is_email_allowed("anyone@other.com") is False

    def test_domain_rule_does_not_match_a_lookalike_suffix(self, allowlist):
        """notexample.com must not satisfy @example.com.

        The rule carries its own leading '@', so the suffix test cannot straddle
        the domain boundary — this is the whole reason the '@' is part of the rule
        rather than stripped off.
        """
        allowlist("@example.com")
        assert is_email_allowed("attacker@notexample.com") is False

    def test_domain_rule_does_not_match_a_subdomain_of_something_else(self, allowlist):
        allowlist("@example.com")
        assert is_email_allowed("attacker@example.com.evil.test") is False

    def test_mixed_exact_and_domain_rules(self, allowlist):
        allowlist("@example.com, contractor@partner.test")
        assert is_email_allowed("rep@example.com") is True
        assert is_email_allowed("contractor@partner.test") is True
        assert is_email_allowed("stranger@partner.test") is False


class TestMissingEmail:
    def test_empty_email_is_refused_when_a_list_is_configured(self, allowlist):
        allowlist("@example.com")
        assert is_email_allowed("") is False
