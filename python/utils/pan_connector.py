import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))
os.environ.setdefault("PANOS_HOSTNAME", "127.0.0.1")
os.environ.setdefault("PANOS_USERNAME", "test-user")
os.environ.setdefault("PANOS_PASSWORD", "test-pass")

import pytest
from unittest.mock import MagicMock, patch
from utils.pan_connector import PanConnector


def test_connector_raises_without_credentials():
    with pytest.raises(ValueError):
        PanConnector(hostname="10.0.0.1", username=None, password=None)


def test_connector_reads_env_credentials(monkeypatch):
    monkeypatch.setenv("PANOS_USERNAME", "admin")
    monkeypatch.setenv("PANOS_PASSWORD", "Passw0rd!")
    monkeypatch.setenv("PANOS_HOSTNAME", "10.0.0.1")
    conn = PanConnector()
    assert conn.username == "admin"
    assert conn.password == "Passw0rd!"


def test_connector_explicit_credentials():
    conn = PanConnector(hostname="10.0.0.1", username="admin", password="pass")
    assert conn.hostname == "10.0.0.1"
    assert conn.username == "admin"


def test_connector_default_device_type():
    conn = PanConnector(hostname="10.0.0.1", username="u", password="p")
    assert conn.device_type == "firewall"


def test_connector_panorama_device_type():
    conn = PanConnector(hostname="10.0.0.1", username="u", password="p", device_type="panorama")
    assert conn.device_type == "panorama"
