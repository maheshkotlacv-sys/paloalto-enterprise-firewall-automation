package firewall.security

import future.keywords.if
import future.keywords.in

# Block SSH from 0.0.0.0/0 to management security group
deny[msg] if {
  some i
  rc := input.resource_changes[i]
  rc.type == "aws_security_group"
  rule := rc.change.after.ingress[_]
  rule.from_port <= 22
  rule.to_port >= 22
  cidr := rule.cidr_blocks[_]
  cidr in {"0.0.0.0/0", "::/0"}
  msg := sprintf("[FW-SG-001] %s: SSH (port 22) must not be open to 0.0.0.0/0.", [rc.address])
}

# Block HTTPS management from 0.0.0.0/0
deny[msg] if {
  some i
  rc := input.resource_changes[i]
  rc.type == "aws_security_group"
  contains(rc.address, "mgmt")
  rule := rc.change.after.ingress[_]
  rule.from_port <= 443
  rule.to_port >= 443
  cidr := rule.cidr_blocks[_]
  cidr == "0.0.0.0/0"
  msg := sprintf("[FW-SG-002] %s: HTTPS management (443) must not be open to 0.0.0.0/0.", [rc.address])
}

# S3 bootstrap bucket must not be public
deny[msg] if {
  some i
  rc := input.resource_changes[i]
  rc.type == "aws_s3_bucket_public_access_block"
  contains(rc.address, "bootstrap")
  rc.change.after.block_public_acls == false
  msg := sprintf("[FW-S3-001] %s: Bootstrap bucket must block public ACLs.", [rc.address])
}

# VM-Series must use IMDSv2
deny[msg] if {
  some i
  rc := input.resource_changes[i]
  rc.type == "aws_instance"
  contains(rc.address, "vmseries")
  rc.change.after.metadata_options.http_tokens != "required"
  msg := sprintf("[FW-EC2-001] %s: VM-Series must enforce IMDSv2 (http_tokens = required).", [rc.address])
}

# EBS root volume must be encrypted
deny[msg] if {
  some i
  rc := input.resource_changes[i]
  rc.type == "aws_instance"
  contains(rc.address, "vmseries")
  vol := rc.change.after.root_block_device[_]
  vol.encrypted == false
  msg := sprintf("[FW-EC2-002] %s: Root EBS volume must be encrypted.", [rc.address])
}
