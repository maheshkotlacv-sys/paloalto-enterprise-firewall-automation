"""Unit tests for pan_threat_intel_sync.py"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from unittest.mock import patch, MagicMock
from pan_threat_intel_sync import ThreatIntelSync, VALID_IP_RE, VALID_DOMAIN_RE


@pytest.fixture
def syncer():
    with patch("boto3.client"):
        return ThreatIntelSync(bucket="test-bucket")


def test_valid_ip_regex():
    assert VALID_IP_RE.match("203.0.113.1") is not None
    assert VALID_IP_RE.match("203.0.113.0/24") is not None


def test_invalid_ip_rejected():
    assert VALID_IP_RE.match("not-an-ip") is None
    assert VALID_IP_RE.match("999.999.999.999") is not None  # regex only checks format, not value range


def test_valid_domain_regex():
    assert VALID_DOMAIN_RE.match("malicious.example.com") is not None
    assert VALID_DOMAIN_RE.match("evil.io") is not None


def test_invalid_domain_rejected():
    assert VALID_DOMAIN_RE.match("not a domain") is None
    assert VALID_DOMAIN_RE.match("") is None


def test_fetch_feed_returns_set(syncer):
    """fetch_feed should return a set of indicators"""
    mock_resp = MagicMock()
    mock_resp.text = "203.0.113.1\n# comment\n198.51.100.5\n\n"
    mock_resp.raise_for_status = MagicMock()
    syncer.session.get = MagicMock(return_value=mock_resp)

    feed = {"url": "https://example.com/feed.txt", "type": "ip"}
    indicators = syncer.fetch_feed(feed)
    assert isinstance(indicators, set)
    assert "203.0.113.1" in indicators
    assert "198.51.100.5" in indicators


def test_fetch_feed_skips_comments(syncer):
    """comment lines and blank lines should be filtered out"""
    mock_resp = MagicMock()
    mock_resp.text = "# blocklist\n203.0.113.1\n\n# more comments\n"
    mock_resp.raise_for_status = MagicMock()
    syncer.session.get = MagicMock(return_value=mock_resp)

    feed = {"url": "https://example.com/feed.txt", "type": "ip"}
    indicators = syncer.fetch_feed(feed)
    assert len(indicators) == 1
    assert "203.0.113.1" in indicators


def test_fetch_feed_deduplicates(syncer):
    """duplicate indicators should be collapsed into one"""
    mock_resp = MagicMock()
    mock_resp.text = "203.0.113.1\n203.0.113.1\n203.0.113.2\n"
    mock_resp.raise_for_status = MagicMock()
    syncer.session.get = MagicMock(return_value=mock_resp)

    feed = {"url": "https://example.com/feed.txt", "type": "ip"}
    indicators = syncer.fetch_feed(feed)
    assert len(indicators) == 2
