#!/usr/bin/env python3
"""
pan_config_backup.py — Automated configuration backup to AWS S3.

Connects to each device, exports the running XML configuration,
and uploads it to S3 with versioning. Keeps a local manifest of
backup timestamps for audit trail.

Usage:
    python3 pan_config_backup.py --devices 10.0.0.1 10.0.0.2 --bucket my-backup-bucket
    python3 pan_config_backup.py --inventory ansible/inventory/hosts.yml --bucket my-backup-bucket
"""

import argparse
import gzip
import json
import logging
import os
import sys
from datetime import datetime
from typing import List, Optional

import boto3
import yaml
from botocore.exceptions import ClientError
from utils.pan_connector import PANConnector

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)


class ConfigBackup:
    def __init__(self, bucket: str, prefix: str = "panos-backups", region: str = "us-east-1"):
        self.bucket = bucket
        self.prefix = prefix
        self.s3 = boto3.client("s3", region_name=region)
        self.manifest: List[dict] = []

    def fetch_config(self, connector: PANConnector) -> Optional[bytes]:
        """Export running config as XML bytes."""
        try:
            result = connector.op_cmd("show config running")
            import xml.etree.ElementTree as ET
            config_bytes = ET.tostring(result, encoding="unicode").encode("utf-8")
            logger.info("Config fetched from %s (%d bytes)", connector.hostname, len(config_bytes))
            return config_bytes
        except Exception as e:
            logger.error("Failed to fetch config from %s: %s", connector.hostname, str(e))
            return None

    def upload_to_s3(self, hostname: str, config_bytes: bytes, compress: bool = True) -> Optional[str]:
        """Upload config to S3, returning the S3 key on success."""
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        ext = ".xml.gz" if compress else ".xml"
        key = f"{self.prefix}/{hostname}/{timestamp}{ext}"

        content = gzip.compress(config_bytes) if compress else config_bytes

        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content,
                ContentType="application/gzip" if compress else "application/xml",
                Metadata={
                    "hostname": hostname,
                    "backup-timestamp": timestamp,
                    "compressed": str(compress),
                },
            )
            logger.info("Uploaded config to s3://%s/%s", self.bucket, key)
            return key
        except ClientError as e:
            logger.error("S3 upload failed for %s: %s", hostname, str(e))
            return None

    def backup_device(self, hostname: str) -> bool:
        """Backup a single device."""
        try:
            with PANConnector(hostname=hostname) as conn:
                sys_info = conn.get_system_info()
                config_bytes = self.fetch_config(conn)
                if config_bytes is None:
                    return False

                s3_key = self.upload_to_s3(hostname, config_bytes)
                if s3_key:
                    self.manifest.append({
                        "hostname": hostname,
                        "device_hostname": sys_info.get("hostname", "unknown"),
                        "panos_version": sys_info.get("sw-version", "unknown"),
                        "s3_key": s3_key,
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": "success",
                    })
                    return True
                return False
        except Exception as e:
            logger.error("Backup failed for %s: %s", hostname, str(e))
            self.manifest.append({
                "hostname": hostname,
                "timestamp": datetime.utcnow().isoformat(),
                "status": "failed",
                "error": str(e),
            })
            return False

    def backup_all(self, hosts: List[str]) -> dict:
        """Backup all devices and return summary."""
        success, failed = 0, 0
        for host in hosts:
            logger.info("Backing up %s...", host)
            if self.backup_device(host):
                success += 1
            else:
                failed += 1

        summary = {
            "total": len(hosts),
            "success": success,
            "failed": failed,
            "timestamp": datetime.utcnow().isoformat(),
            "manifest": self.manifest,
        }

        manifest_key = f"{self.prefix}/manifest-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}.json"
        try:
            self.s3.put_object(
                Bucket=self.bucket,
                Key=manifest_key,
                Body=json.dumps(summary, indent=2).encode(),
                ContentType="application/json",
            )
            logger.info("Manifest uploaded to s3://%s/%s", self.bucket, manifest_key)
        except ClientError as e:
            logger.error("Manifest upload failed: %s", str(e))

        return summary


def load_hosts_from_inventory(inventory_file: str) -> List[str]:
    """Parse Ansible YAML inventory and extract ansible_host values."""
    with open(inventory_file) as f:
        inventory = yaml.safe_load(f)

    hosts = []
    def extract_hosts(node):
        if isinstance(node, dict):
            if "ansible_host" in node:
                hosts.append(node["ansible_host"])
            for v in node.values():
                extract_hosts(v)
        elif isinstance(node, list):
            for item in node:
                extract_hosts(item)

    extract_hosts(inventory)
    return list(set(hosts))


def main():
    parser = argparse.ArgumentParser(description="PAN-OS configuration backup to S3")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--devices", nargs="+", help="Device IPs or hostnames")
    group.add_argument("--inventory", help="Path to Ansible inventory YAML file")
    parser.add_argument("--bucket", required=True, help="S3 bucket name for backups")
    parser.add_argument("--prefix", default="panos-backups", help="S3 key prefix")
    parser.add_argument("--region", default="us-east-1", help="AWS region")
    args = parser.parse_args()

    hosts = args.devices if args.devices else load_hosts_from_inventory(args.inventory)
    logger.info("Backing up %d devices", len(hosts))

    backup = ConfigBackup(bucket=args.bucket, prefix=args.prefix, region=args.region)
    summary = backup.backup_all(hosts)

    logger.info("Backup complete: %d/%d successful", summary["success"], summary["total"])
    if summary["failed"] > 0:
        logger.warning("%d device(s) failed backup — check manifest.", summary["failed"])
        sys.exit(1)


if __name__ == "__main__":
    main()
