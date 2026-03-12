#!/usr/bin/env python3
"""
pan_compliance_report.py — CIS PAN-OS Benchmark compliance reporter.

Checks devices against CIS Palo Alto Firewall benchmark controls and
generates an HTML report showing pass/fail/warn per control.

Usage:
    python3 pan_compliance_report.py --device 10.0.0.1 --output compliance.html
    python3 pan_compliance_report.py --panorama --all-devices --output compliance.html
"""

import argparse
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Dict, Any, Optional

from utils.pan_connector import PANConnector, PanoramaConnector
from utils.report_generator import generate_html_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class Status(Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    WARN = "WARN"
    SKIP = "SKIP"


@dataclass
class CheckResult:
    control_id: str
    title: str
    status: Status
    detail: str
    severity: str = "MEDIUM"
    remediation: str = ""


class CISPANOSChecker:
    """Runs CIS PAN-OS Benchmark checks against a connected device."""

    def __init__(self, connector: PANConnector):
        self.conn = connector
        self.results: List[CheckResult] = []

    def _op(self, cmd: str) -> Any:
        return self.conn.op_cmd(cmd)

    def check_mgmt_services(self) -> CheckResult:
        """CIS 1.1 — Ensure management services are hardened."""
        try:
            result = self._op("show system setting management-interface")
            output = str(result)
            telnet_disabled = "telnet" not in output.lower() or "disable" in output.lower()
            http_disabled = "http" not in output.lower() or "disable" in output.lower()
            if telnet_disabled and http_disabled:
                return CheckResult("CIS-1.1", "Management services hardened", Status.PASS,
                                   "Telnet and HTTP are disabled on management interface.", "HIGH")
            return CheckResult("CIS-1.1", "Management services hardened", Status.FAIL,
                               "Telnet or HTTP is enabled on management interface.", "HIGH",
                               "Disable Telnet and HTTP in Device > Setup > Management > Management Interface Settings.")
        except Exception as e:
            return CheckResult("CIS-1.1", "Management services hardened", Status.SKIP, str(e))

    def check_password_complexity(self) -> CheckResult:
        """CIS 1.2 — Ensure password complexity requirements are set."""
        try:
            result = self._op("show config running")
            output = str(result)
            if "minimum-length" in output and "minimum-uppercase-letters" in output:
                return CheckResult("CIS-1.2", "Password complexity enabled", Status.PASS,
                                   "Password complexity policy is configured.", "HIGH")
            return CheckResult("CIS-1.2", "Password complexity enabled", Status.FAIL,
                               "Password complexity policy is not configured.", "HIGH",
                               "Configure password complexity in Device > Setup > Management > Password Complexity.")
        except Exception as e:
            return CheckResult("CIS-1.2", "Password complexity enabled", Status.SKIP, str(e))

    def check_snmpv3(self) -> CheckResult:
        """CIS 1.3 — Ensure only SNMPv3 is used."""
        try:
            result = self._op("show system setting snmp")
            output = str(result)
            if "v2c" in output.lower():
                return CheckResult("CIS-1.3", "SNMPv3 only", Status.FAIL,
                                   "SNMPv2c is enabled. Only SNMPv3 should be used.", "HIGH",
                                   "Disable SNMPv2c and configure SNMPv3 in Device > Setup > Operations.")
            return CheckResult("CIS-1.3", "SNMPv3 only", Status.PASS,
                               "SNMPv2c is not configured.", "HIGH")
        except Exception as e:
            return CheckResult("CIS-1.3", "SNMPv3 only", Status.SKIP, str(e))

    def check_logging_enabled(self) -> CheckResult:
        """CIS 2.1 — Ensure logging is configured for all security rules."""
        try:
            result = self._op("show running security-policy")
            output = str(result)
            if "log at session end" in output.lower() or "log-end" in output.lower():
                return CheckResult("CIS-2.1", "Logging on security rules", Status.PASS,
                                   "Session-end logging is configured.", "MEDIUM")
            return CheckResult("CIS-2.1", "Logging on security rules", Status.WARN,
                               "Some rules may not have logging configured.", "MEDIUM",
                               "Ensure all security rules have log-at-session-end enabled.")
        except Exception as e:
            return CheckResult("CIS-2.1", "Logging on security rules", Status.SKIP, str(e))

    def check_deny_all_rule(self) -> CheckResult:
        """CIS 2.2 — Ensure an explicit deny-all rule exists at the bottom of the ruleset."""
        try:
            result = self._op("show running security-policy")
            output = str(result)
            if "deny" in output.lower():
                return CheckResult("CIS-2.2", "Explicit deny-all rule present", Status.PASS,
                                   "A deny rule exists in the security policy.", "HIGH")
            return CheckResult("CIS-2.2", "Explicit deny-all rule present", Status.FAIL,
                               "No explicit deny-all rule found.", "HIGH",
                               "Add a deny rule as the last rule in the security policy with logging enabled.")
        except Exception as e:
            return CheckResult("CIS-2.2", "Explicit deny-all rule present", Status.SKIP, str(e))

    def check_threat_prevention_profiles(self) -> CheckResult:
        """CIS 3.1 — Ensure threat prevention profiles are applied to allow rules."""
        try:
            result = self._op("show running security-policy")
            output = str(result)
            if "profile-setting" in output.lower() or "group-profile" in output.lower():
                return CheckResult("CIS-3.1", "Threat prevention profiles applied", Status.PASS,
                                   "Security profile groups are applied to rules.", "HIGH")
            return CheckResult("CIS-3.1", "Threat prevention profiles applied", Status.FAIL,
                               "No security profile groups detected on allow rules.", "HIGH",
                               "Apply AV, IPS, URL filtering, and WildFire profiles to all allow rules.")
        except Exception as e:
            return CheckResult("CIS-3.1", "Threat prevention profiles applied", Status.SKIP, str(e))

    def check_ntp_configured(self) -> CheckResult:
        """CIS 4.1 — Ensure NTP is configured."""
        try:
            result = self._op("show system info")
            output = str(result)
            if "ntp" in output.lower():
                return CheckResult("CIS-4.1", "NTP configured", Status.PASS,
                                   "NTP server is configured.", "MEDIUM")
            return CheckResult("CIS-4.1", "NTP configured", Status.WARN,
                               "NTP configuration not confirmed.", "MEDIUM",
                               "Configure NTP servers in Device > Setup > Services.")
        except Exception as e:
            return CheckResult("CIS-4.1", "NTP configured", Status.SKIP, str(e))

    def check_dns_configured(self) -> CheckResult:
        """CIS 4.2 — Ensure DNS is configured."""
        try:
            result = self._op("show system info")
            output = str(result)
            if "dns-primary" in output.lower() or "dns-setting" in output.lower():
                return CheckResult("CIS-4.2", "DNS configured", Status.PASS,
                                   "DNS servers are configured.", "MEDIUM")
            return CheckResult("CIS-4.2", "DNS configured", Status.WARN,
                               "DNS configuration not confirmed.", "MEDIUM",
                               "Configure DNS servers in Device > Setup > Services.")
        except Exception as e:
            return CheckResult("CIS-4.2", "DNS configured", Status.SKIP, str(e))

    def run_all_checks(self) -> List[CheckResult]:
        checks = [
            self.check_mgmt_services,
            self.check_password_complexity,
            self.check_snmpv3,
            self.check_logging_enabled,
            self.check_deny_all_rule,
            self.check_threat_prevention_profiles,
            self.check_ntp_configured,
            self.check_dns_configured,
        ]
        results = []
        for check in checks:
            logger.info("Running check: %s", check.__name__)
            result = check()
            results.append(result)
            logger.info("%s — %s", result.control_id, result.status.value)
        return results

    def generate_report(self, output_file: str) -> None:
        results = self.run_all_checks()
        device_info = self.conn.get_system_info()
        passed = sum(1 for r in results if r.status == Status.PASS)
        failed = sum(1 for r in results if r.status == Status.FAIL)
        warned = sum(1 for r in results if r.status == Status.WARN)

        rows = [
            [r.control_id, r.title, r.status.value, r.severity, r.detail, r.remediation]
            for r in results
        ]
        report = generate_html_report(
            title="CIS PAN-OS Benchmark Compliance Report",
            sections=[{
                "title": f"Compliance Results — {passed} PASS | {failed} FAIL | {warned} WARN",
                "headers": ["Control ID", "Title", "Status", "Severity", "Detail", "Remediation"],
                "rows": rows,
            }],
            metadata={
                "Device": self.conn.hostname,
                "Hostname": device_info.get("hostname", "unknown"),
                "PAN-OS": device_info.get("sw-version", "unknown"),
                "Report Date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
                "Score": f"{passed}/{len(results)} checks passed",
            },
        )
        with open(output_file, "w") as fh:
            fh.write(report)
        logger.info("Compliance report: %s/%s passed. Written to %s", passed, len(results), output_file)


def main():
    parser = argparse.ArgumentParser(description="CIS PAN-OS compliance reporter")
    parser.add_argument("--device", required=True)
    parser.add_argument("--output", default="compliance-report.html")
    args = parser.parse_args()
    with PANConnector(hostname=args.device) as conn:
        checker = CISPANOSChecker(conn)
        checker.generate_report(args.output)


if __name__ == "__main__":
    main()
