import pytest
from unittest.mock import MagicMock
from pan_rule_audit import RuleAuditor


class MockRule:
    def __init__(self, name, application=None, service="application-default",
                 log_setting=None, log_end=True, disabled=False, action="allow"):
        self.name = name
        self.application = application or ["ssl"]
        self.service = service
        self.log_setting = log_setting
        self.log_end = log_end
        self.disabled = disabled
        self.action = action


def make_auditor():
    return RuleAuditor(MagicMock())


def test_any_application_detected():
    assert make_auditor().check_any_application(MockRule("r", application=["any"])) is True


def test_specific_application_not_flagged():
    assert make_auditor().check_any_application(MockRule("r", application=["ssl"])) is False


def test_no_logging_detected():
    assert make_auditor().check_no_logging(MockRule("r", log_setting=None, log_end=False)) is True


def test_logging_present_not_flagged():
    assert make_auditor().check_no_logging(MockRule("r", log_end=True)) is False


def test_disabled_rule_detected():
    assert make_auditor().check_disabled(MockRule("r", disabled=True)) is True


def test_enabled_rule_not_flagged():
    assert make_auditor().check_disabled(MockRule("r", disabled=False)) is False
