#!/usr/bin/env python3
"""
pan_log_analyzer.py — Parse PAN-OS threat logs and generate alerts.

Queries threat logs via the PAN-OS API, identifies high-severity events,
and outputs a report. Designed to be run on a schedule (cron/GitHub Actions).

Usage:
    python3 pan_log_analyzer.py --device 10.0.0.1 --severity high --hours 24
"""

import argparse
import logging
import os
import xml.etree.ElementTree as ET
from collections import Counter
from datetime import datetime, timedelta
from typing import List, Dict

from utils.pan_connector import PANConnector
from utils.report_generator import generate_html_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

SEVERITY_LEVELS = {"critical": 5, "high": 4, "medium": 3, "low": 2, "informational": 1}


class LogAnalyzer:
    def __init__(self, connector: PANConnector):
        self.conn = connector

    def query_threat_logs(self, hours: int = 24, min_severity: str = "high") -> List[Dict]:
        """Query threat logs from PAN-OS."""
        min_level = SEVERITY_LEVELS.get(min_severity.lower(), 4)
        cmd = (
            f"<show><log><threat><nlogs>500</nlogs>"
            f"<query>(severity geq {min_severity})</query>"
            f"</threat></log></show>"
        )
        try:
            result = self.conn.op_cmd(cmd)
            entries = []
            for entry in result.findall(".//entry"):
                severity = entry.findtext("severity", "unknown")
                if SEVERITY_LEVELS.get(severity, 0) >= min_level:
                    entries.append({
                        "time": entry.findtext("receive_time", ""),
                        "src_ip": entry.findtext("src", ""),
                        "dst_ip": entry.findtext("dst", ""),
                        "threat_name": entry.findtext("threatid", ""),
                        "severity": severity,
                        "action": entry.findtext("action", ""),
                        "app": entry.findtext("app", ""),
                        "rule": entry.findtext("rule", ""),
                        "direction": entry.findtext("direction", ""),
                    })
            logger.info("Retrieved %d threat log entries (>= %s)", len(entries), min_severity)
            return entries
        except Exception as e:
            logger.error("Failed to query threat logs: %s", str(e))
            return []

    def analyze(self, logs: List[Dict]) -> Dict:
        """Generate analysis summary from log entries."""
        if not logs:
            return {"total": 0, "top_threats": [], "top_sources": [], "top_destinations": []}

        threat_counts = Counter(e["threat_name"] for e in logs)
        src_counts = Counter(e["src_ip"] for e in logs if e["src_ip"])
        dst_counts = Counter(e["dst_ip"] for e in logs if e["dst_ip"])
        critical_count = sum(1 for e in logs if e["severity"] == "critical")
        blocked_count = sum(1 for e in logs if "block" in e["action"].lower() or "drop" in e["action"].lower())

        return {
            "total": len(logs),
            "critical_count": critical_count,
            "blocked_count": blocked_count,
            "allowed_count": len(logs) - blocked_count,
            "top_threats": threat_counts.most_common(10),
            "top_sources": src_counts.most_common(10),
            "top_destinations": dst_counts.most_common(10),
        }

    def generate_report(self, output_file: str, hours: int = 24, min_severity: str = "high") -> None:
        logs = self.query_threat_logs(hours=hours, min_severity=min_severity)
        analysis = self.analyze(logs)
        device_info = self.conn.get_system_info()

        log_rows = [
            [e["time"], e["src_ip"], e["dst_ip"], e["threat_name"], e["severity"], e["action"], e["app"]]
            for e in sorted(logs, key=lambda x: x["severity"], reverse=True)[:100]
        ]

        report = generate_html_report(
            title="PAN-OS Threat Log Analysis",
            sections=[
                {
                    "title": f"Summary — {analysis['total']} events in last {hours}h",
                    "description": (
                        f"Critical: {analysis.get('critical_count', 0)} | "
                        f"Blocked: {analysis.get('blocked_count', 0)} | "
                        f"Allowed: {analysis.get('allowed_count', 0)}"
                    ),
                },
                {
                    "title": "Top 100 Threat Events",
                    "headers": ["Time", "Source IP", "Dest IP", "Threat", "Severity", "Action", "App"],
                    "rows": log_rows,
                },
            ],
            metadata={
                "Device": self.conn.hostname,
                "Hostname": device_info.get("hostname", "unknown"),
                "PAN-OS": device_info.get("sw-version", "unknown"),
                "Period": f"Last {hours} hours",
                "Min Severity": min_severity,
            },
        )
        with open(output_file, "w") as fh:
            fh.write(report)
        logger.info("Log analysis report written to %s", output_file)


def main():
    parser = argparse.ArgumentParser(description="PAN-OS threat log analyzer")
    parser.add_argument("--device", required=True)
    parser.add_argument("--severity", default="high", choices=["critical", "high", "medium", "low"])
    parser.add_argument("--hours", type=int, default=24)
    parser.add_argument("--output", default="threat-log-report.html")
    args = parser.parse_args()
    with PANConnector(hostname=args.device) as conn:
        analyzer = LogAnalyzer(conn)
        analyzer.generate_report(args.output, hours=args.hours, min_severity=args.severity)


if __name__ == "__main__":
    main()
