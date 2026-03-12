#!/usr/bin/env python3
"""Unit tests for pan_connector.py"""

import os
import pytest
from unittest.mock import MagicMock, patch

os.environ.setdefault("PANOS_USERNAME", "test-user")
os.environ.setdefault("PANOS_PASSWORD", "test-pass")
os.environ.setdefault("PANORAMA_HOSTNAME", "127.0.0.1")

import sys
sys.path.insert(0, "python")
from utils.pan_connector import PANConnector, PanoramaConnector


def test_connector_raises_without_credentials():
    with pytest.raises(ValueError, match="environment variables"):
        _ = PANConnector(hostname="10.0.0.1", username=None, password=None, api_key=None)


def test_connector_accepts_env_credentials(monkeypatch):
    monkeypatch.setenv("PANOS_USERNAME", "admin")
    monkeypatch.setenv("PANOS_PASSWORD", "Passw0rd!")
    conn = PANConnector(hostname="10.0.0.1")
    assert conn.username == "admin"
    assert conn.password == "Passw0rd!"


def test_panorama_connector_requires_hostname(monkeypatch):
    monkeypatch.delenv("PANORAMA_HOSTNAME", raising=False)
    with pytest.raises(ValueError, match="PANORAMA_HOSTNAME"):
        _ = PanoramaConnector(hostname=None)


def test_panorama_connector_uses_env_hostname(monkeypatch):
    monkeypatch.setenv("PANORAMA_HOSTNAME", "panorama.example.com")
    monkeypatch.setenv("PANOS_USERNAME", "admin")
    monkeypatch.setenv("PANOS_PASSWORD", "pass")
    conn = PanoramaConnector()
    assert conn.hostname == "panorama.example.com"
