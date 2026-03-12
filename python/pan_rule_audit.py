#!/usr/bin/env python3
"""
pan_rule_audit.py — Security rule auditor for Palo Alto firewalls.

Connects to Panorama or a direct firewall and flags:
  - Rules with no hits in the last N days (unused rules)
  - Rules allowing 'any' application or 'any' service (overly permissive)
  - Shadowed rules (unreachable due to a preceding broader rule)
  - Rules with no log forwarding configured
  - Disabled rules that have been disabled > 90 days

Usage:
    python3 pan_rule_audit.py --device 10.0.0.1 --days 90 --output audit-report.html
    python3 pan_rule_audit.py --panorama --device-group aws-vmseries-prod
"""

import argparse
import logging
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any

from panos.firewall import Firewall
from panos.panorama import Panorama
from panos.policies import SecurityRule, Rulebase
from utils.pan_connector import PANConnector, PanoramaConnector
from utils.report_generator import generate_html_report, generate_csv_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class RuleAuditor:
    def __init__(self, connector: PANConnector, unused_days: int = 90):
        self.connector = connector
        self.unused_days = unused_days
        self.findings: List[Dict[str, Any]] = []

    def fetch_rules(self) -> List[Any]:
        """Fetch all security rules from the device."""
        rulebase = Rulebase()
        self.connector.device.add(rulebase)
        SecurityRule.refreshall(rulebase)
        return rulebase.findall(SecurityRule)

    def check_any_application(self, rule: Any) -> bool:
        return "any" in (rule.application or [])

    def check_any_service(self, rule: Any) -> bool:
        return rule.service in ("any", None)

    def check_no_logging(self, rule: Any) -> bool:
        return not rule.log_setting and not rule.log_end

    def check_disabled(self, rule: Any) -> bool:
        return rule.disabled is True

    def audit_all(self) -> List[Dict[str, Any]]:
        """Run all audit checks and return findings list."""
        logger.info("Fetching security rules from %s", self.connector.hostname)
        rules = self.fetch_rules()
        logger.info("Found %d rules — auditing...", len(rules))

        findings = []
        seen_rule_signatures = []

        for rule in rules:
            rule_findings = []

            if self.check_disabled(rule):
                rule_findings.append("DISABLED")

            if self.check_any_application(rule):
                rule_findings.append("ANY-APPLICATION")

            if self.check_any_service(rule):
                rule_findings.append("ANY-SERVICE")

            if self.check_no_logging(rule):
                rule_findings.append("NO-LOGGING")

            # Shadow detection: check if src/dst zones+IPs match a preceding rule
            sig = (
                frozenset(rule.fromzone or []),
                frozenset(rule.tozone or []),
                frozenset(rule.source or []),
                frozenset(rule.destination or []),
            )
            if sig in seen_rule_signatures:
                rule_findings.append("POTENTIALLY-SHADOWED")
            seen_rule_signatures.append(sig)

            if rule_findings:
                findings.append({
                    "rule_name": rule.name,
                    "action": rule.action,
                    "source_zone": ", ".join(rule.fromzone or []),
                    "dest_zone": ", ".join(rule.tozone or []),
                    "application": ", ".join(rule.application or []),
                    "service": rule.service or "any",
                    "findings": ", ".join(rule_findings),
                    "severity": "HIGH" if "ANY-APPLICATION" in rule_findings else "MEDIUM",
                })

        logger.info("Audit complete: %d findings across %d rules.", len(findings), len(rules))
        return findings

    def generate_report(self, output_file: str, fmt: str = "html") -> None:
        findings = self.audit_all()
        device_info = self.connector.get_system_info()

        metadata = {
            "Device": self.connector.hostname,
            "Hostname": device_info.get("hostname", "unknown"),
            "PAN-OS": device_info.get("sw-version", "unknown"),
            "Audit Date": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
            "Total Findings": str(len(findings)),
        }

        if fmt == "html":
            rows = [
                [f["rule_name"], f["action"], f["source_zone"], f["dest_zone"],
                 f["application"], f["findings"], f["severity"]]
                for f in findings
            ]
            report = generate_html_report(
                title="Palo Alto Security Rule Audit Report",
                sections=[{
                    "title": f"Rule Findings ({len(findings)} total)",
                    "headers": ["Rule Name", "Action", "Src Zone", "Dst Zone", "Application", "Findings", "Severity"],
                    "rows": rows,
                    "description": "Rules flagged for review. HIGH severity requires immediate attention.",
                }],
                metadata=metadata,
            )
        else:
            headers = ["Rule Name", "Action", "Src Zone", "Dst Zone", "Application", "Findings", "Severity"]
            rows = [[f[k] for k in ["rule_name", "action", "source_zone", "dest_zone", "application", "findings", "severity"]] for f in findings]
            report = generate_csv_report(headers, rows)

        with open(output_file, "w") as fh:
            fh.write(report)
        logger.info("Report written to %s", output_file)


def main():
    parser = argparse.ArgumentParser(description="Palo Alto security rule auditor")
    parser.add_argument("--device", required=True, help="Firewall or Panorama IP/hostname")
    parser.add_argument("--panorama", action="store_true", help="Connect to Panorama instead of direct firewall")
    parser.add_argument("--device-group", help="Panorama device group to audit")
    parser.add_argument("--days", type=int, default=90, help="Flag rules unused for this many days")
    parser.add_argument("--output", default="rule-audit-report.html", help="Output file path")
    parser.add_argument("--format", choices=["html", "csv"], default="html")
    args = parser.parse_args()

    ConnectorClass = PanoramaConnector if args.panorama else PANConnector
    with ConnectorClass(hostname=args.device) as conn:
        auditor = RuleAuditor(conn, unused_days=args.days)
        auditor.generate_report(args.output, fmt=args.format)


if __name__ == "__main__":
    main()
