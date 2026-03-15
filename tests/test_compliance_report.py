#!/usr/bin/env python3
"""Unit tests for pan_compliance_report.py"""

import sys
import os

os.environ.setdefault("PANOS_USERNAME", "test")
os.environ.setdefault("PANOS_PASSWORD", "test")

sys.path.insert(0, "python")

import pytest
from unittest.mock import MagicMock
from pan_compliance_report import CISPANOSChecker, Status


def make_checker_with_mock(op_return_text=""):
    conn = MagicMock()
    mock_result = MagicMock()
    mock_result.__str__ = lambda self: op_return_text
    conn.op_cmd.return_value = mock_result
    conn.get_system_info.return_value = {"hostname": "test-fw", "sw-version": "11.1.2"}
    return CISPANOSChecker(conn)


def test_mgmt_services_pass_when_telnet_disabled():
    checker = make_checker_with_mock("management interface: https enabled, telnet disabled")
    result = checker.check_mgmt_services()
    assert result.status == Status.PASS


def test_deny_all_rule_pass():
    checker = make_checker_with_mock("deny-any-any-log deny action=deny")
    result = checker.check_deny_all_rule()
    assert result.status == Status.PASS


def test_deny_all_rule_fail_when_missing():
    checker = make_checker_with_mock("allow-web-browsing allow")
    result = checker.check_deny_all_rule()
    assert result.status == Status.FAIL
