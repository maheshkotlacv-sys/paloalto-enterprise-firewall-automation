#!/usr/bin/env python3
"""Unit tests for pan_rule_audit.py"""

import sys
import os

os.environ.setdefault("PANOS_USERNAME", "test")
os.environ.setdefault("PANOS_PASSWORD", "test")

sys.path.insert(0, "python")

from unittest.mock import MagicMock, patch
import pytest


class MockRule:
    def __init__(self, name, application=None, service="application-default",
                 log_setting=None, log_end=True, disabled=False,
                 fromzone=None, tozone=None, source=None, destination=None, action="allow"):
        self.name = name
        self.application = application or ["ssl"]
        self.service = service
        self.log_setting = log_setting
        self.log_end = log_end
        self.disabled = disabled
        self.fromzone = fromzone or ["trust"]
        self.tozone = tozone or ["untrust"]
        self.source = source or ["any"]
        self.destination = destination or ["any"]
        self.action = action


def test_any_application_detection():
    from pan_rule_audit import RuleAuditor
    auditor = RuleAuditor(MagicMock())
    rule_with_any = MockRule("test-any", application=["any"])
    rule_specific = MockRule("test-specific", application=["ssl", "web-browsing"])
    assert auditor.check_any_application(rule_with_any) is True
    assert auditor.check_any_application(rule_specific) is False


def test_no_logging_detection():
    from pan_rule_audit import RuleAuditor
    auditor = RuleAuditor(MagicMock())
    rule_no_log = MockRule("test-nolog", log_setting=None, log_end=False)
    rule_with_log = MockRule("test-logged", log_end=True)
    assert auditor.check_no_logging(rule_no_log) is True
    assert auditor.check_no_logging(rule_with_log) is False


def test_disabled_rule_detection():
    from pan_rule_audit import RuleAuditor
    auditor = RuleAuditor(MagicMock())
    assert auditor.check_disabled(MockRule("disabled", disabled=True)) is True
    assert auditor.check_disabled(MockRule("enabled", disabled=False)) is False
