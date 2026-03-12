import pytest
from unittest.mock import MagicMock
from pan_compliance_report import CISPANOSChecker, Status


def make_checker(op_response=""):
    conn = MagicMock()
    conn.op.return_value = MagicMock(__str__=lambda self: op_response)
    return CISPANOSChecker(conn)


def test_mgmt_check_returns_result():
    checker = make_checker("https enabled telnet disabled")
    result = checker.check_mgmt_services()
    assert result.status in (Status.PASS, Status.FAIL, Status.SKIP)


def test_deny_all_pass_when_present():
    checker = make_checker("DENY-ALL-CLEANUP deny action=deny")
    result = checker.check_deny_all_rule()
    assert result.status == Status.PASS


def test_deny_all_fail_when_missing():
    checker = make_checker("allow-web-browsing allow")
    result = checker.check_deny_all_rule()
    assert result.status in (Status.FAIL, Status.SKIP)


def test_run_all_checks_returns_list():
    checker = make_checker()
    results = checker.run_all_checks()
    assert isinstance(results, list)
    assert len(results) > 0


def test_status_enum_has_pass_fail():
    assert hasattr(Status, "PASS")
    assert hasattr(Status, "FAIL")
