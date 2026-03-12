"""Unit tests for pan_threat_intel_sync.py"""
import pytest
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

from unittest.mock import patch, MagicMock
from pan_threat_intel_sync import ThreatIntelSync


@pytest.fixture
def syncer():
    with patch("boto3.client"):
        return ThreatIntelSync(edl_bucket="test-bucket")


def test_valid_ip_passes(syncer):
    assert syncer.is_valid_ip("203.0.113.1") is True
    assert syncer.is_valid_ip("203.0.113.0/24") is True


def test_invalid_ip_rejected(syncer):
    assert syncer.is_valid_ip("not-an-ip") is False
    assert syncer.is_valid_ip("999.999.999.999") is False


def test_rfc1918_whitelisted(syncer):
    assert syncer.is_whitelisted_ip("10.10.10.10") is True
    assert syncer.is_whitelisted_ip("192.168.1.1") is True
    assert syncer.is_whitelisted_ip("172.20.0.1") is True


def test_public_ip_not_whitelisted(syncer):
    assert syncer.is_whitelisted_ip("203.0.113.1") is False


def test_valid_domain_passes(syncer):
    assert syncer.is_valid_domain("malicious.example.com") is True
    assert syncer.is_valid_domain("evil.io") is True


def test_invalid_domain_rejected(syncer):
    assert syncer.is_valid_domain("not a domain") is False
    assert syncer.is_valid_domain("") is False


def test_whitelisted_domain_excluded(syncer):
    assert syncer.is_whitelisted_domain("login.microsoftonline.microsoft.com") is True
    assert syncer.is_whitelisted_domain("s3.amazonaws.com") is True


def test_process_ip_feed_filters_whitelist(syncer):
    raw = ["203.0.113.1", "10.0.0.1", "192.168.1.1", "198.51.100.5"]
    valid, skipped_invalid, skipped_whitelist = syncer.process_ip_feed(raw)
    assert "203.0.113.1" in valid
    assert "198.51.100.5" in valid
    assert skipped_whitelist == 2


def test_process_ip_feed_deduplicates(syncer):
    raw = ["203.0.113.1", "203.0.113.1", "203.0.113.2"]
    valid, _, _ = syncer.process_ip_feed(raw)
    assert len(valid) == 2
