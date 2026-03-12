#!/usr/bin/env python3
"""
pan_threat_intel_sync.py — Threat intelligence IOC sync to Palo Alto EDL.

Pulls IOC feeds (IPs, domains, URLs) from threat intel sources and
pushes them to an AWS S3-hosted External Dynamic List consumed by
Palo Alto firewalls. Supports multiple feed formats.

Usage:
    python3 pan_threat_intel_sync.py --feeds config/feeds.yml --bucket my-edl-bucket
"""

import argparse
import hashlib
import json
import logging
import os
import re
import time
from datetime import datetime
from typing import List, Dict, Set
from urllib.parse import urlparse

import boto3
import requests
import yaml
from botocore.exceptions import ClientError

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger(__name__)

VALID_IP_RE = re.compile(r"^(\d{1,3}\.){3}\d{1,3}(/\d{1,2})?$")
VALID_DOMAIN_RE = re.compile(r"^([a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}$")


class ThreatIntelSync:
    def __init__(self, bucket: str, region: str = "us-east-1"):
        self.bucket = bucket
        self.s3 = boto3.client("s3", region_name=region)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "PAN-EDL-Sync/1.0"})

    def fetch_feed(self, feed: Dict) -> Set[str]:
        """Fetch a single IOC feed and return a set of validated indicators."""
        url = feed["url"]
        feed_type = feed.get("type", "ip")
        logger.info("Fetching %s feed: %s", feed_type, url)

        try:
            resp = self.session.get(url, timeout=30)
            resp.raise_for_status()
            raw_lines = resp.text.splitlines()
        except requests.RequestException as e:
            logger.error("Failed to fetch %s: %s", url, str(e))
            return set()

        indicators = set()
        for line in raw_lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            # Strip inline comments
            indicator = line.split("#")[0].strip().split()[0] if line else ""
            if not indicator:
                continue

            if feed_type == "ip" and VALID_IP_RE.match(indicator):
                indicators.add(indicator)
            elif feed_type == "domain" and VALID_DOMAIN_RE.match(indicator):
                indicators.add(indicator)
            elif feed_type == "url":
                parsed = urlparse(indicator if "://" in indicator else f"http://{indicator}")
                if parsed.netloc:
                    indicators.add(indicator)

        logger.info("Fetched %d valid %s indicators from %s", len(indicators), feed_type, url)
        return indicators

    def upload_edl(self, indicators: Set[str], edl_name: str, edl_type: str) -> Optional[str]:
        """Upload deduplicated, sorted indicator list to S3 as EDL."""
        if not indicators:
            logger.warning("No indicators to upload for EDL %s", edl_name)
            return None

        sorted_iocs = sorted(indicators)
        content = "
".join(sorted_iocs) + "
"
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
        timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
        key = f"edl/{edl_type}/{edl_name}.txt"
        archive_key = f"edl/archive/{edl_type}/{edl_name}-{timestamp}-{content_hash}.txt"

        try:
            # Upload current EDL (overwrites previous — firewalls poll this URL)
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content.encode("utf-8"),
                ContentType="text/plain",
                CacheControl="no-cache, no-store",
                Metadata={
                    "edl-name": edl_name,
                    "indicator-count": str(len(sorted_iocs)),
                    "updated": timestamp,
                    "content-hash": content_hash,
                },
            )
            # Archive copy for audit trail
            self.s3.put_object(
                Bucket=self.bucket,
                Key=archive_key,
                Body=content.encode("utf-8"),
                ContentType="text/plain",
            )
            edl_url = f"https://{self.bucket}.s3.amazonaws.com/{key}"
            logger.info(
                "EDL %s uploaded: %d indicators. URL: %s", edl_name, len(sorted_iocs), edl_url
            )
            return edl_url
        except ClientError as e:
            logger.error("S3 upload failed for EDL %s: %s", edl_name, str(e))
            return None

    def sync_all(self, feeds_config: List[Dict]) -> Dict:
        """Process all configured feeds and produce EDL files."""
        results = {}
        combined: Dict[str, Set[str]] = {"ip": set(), "domain": set(), "url": set()}

        for feed in feeds_config:
            indicators = self.fetch_feed(feed)
            feed_type = feed.get("type", "ip")
            combined[feed_type].update(indicators)

        for edl_type, indicators in combined.items():
            if indicators:
                edl_name = f"enterprise-blocklist-{edl_type}"
                url = self.upload_edl(indicators, edl_name, edl_type)
                results[edl_type] = {
                    "count": len(indicators),
                    "edl_name": edl_name,
                    "s3_url": url,
                }

        return results


DEFAULT_FEEDS = [
    {"name": "emerging-threats-compromised", "url": "https://rules.emergingthreats.net/blockrules/compromised-ips.txt", "type": "ip"},
    {"name": "feodo-c2-ips", "url": "https://feodotracker.abuse.ch/downloads/ipblocklist.txt", "type": "ip"},
    {"name": "urlhaus-domains", "url": "https://urlhaus.abuse.ch/downloads/hostfile/", "type": "domain"},
]


def main():
    parser = argparse.ArgumentParser(description="Sync threat intel IOC feeds to PAN-OS EDL on S3")
    parser.add_argument("--feeds", help="YAML file with feed definitions")
    parser.add_argument("--bucket", required=True, help="S3 bucket to host EDL files")
    parser.add_argument("--region", default="us-east-1")
    args = parser.parse_args()

    if args.feeds:
        with open(args.feeds) as f:
            feeds_config = yaml.safe_load(f)
    else:
        feeds_config = DEFAULT_FEEDS
        logger.info("Using default feed list (%d feeds)", len(feeds_config))

    syncer = ThreatIntelSync(bucket=args.bucket, region=args.region)
    results = syncer.sync_all(feeds_config)

    logger.info("Sync complete: %s", json.dumps(results, indent=2))


if __name__ == "__main__":
    main()
