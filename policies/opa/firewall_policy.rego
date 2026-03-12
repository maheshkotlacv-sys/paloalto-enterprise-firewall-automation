package firewall.security

# sg-001: no public ingress except 80/443
deny[msg] {
  rc := input.resource_changes[_]
  rc.type == "aws_security_group"
  ingress := rc.change.after.ingress[_]
  not ingress.from_port == 80
  not ingress.from_port == 443
  cidr := ingress.cidr_blocks[_]
  cidr == "0.0.0.0/0"
  msg := sprintf("[SG-001] '%s': public ingress only allowed on 80/443", [rc.address])
}

# sg-002: ssh never from internet
deny[msg] {
  rc := input.resource_changes[_]
  rc.type == "aws_security_group"
  ingress := rc.change.after.ingress[_]
  ingress.from_port <= 22
  ingress.to_port >= 22
  cidr := ingress.cidr_blocks[_]
  cidr == "0.0.0.0/0"
  msg := sprintf("[SG-002] '%s': ssh open to internet", [rc.address])
}

# sg-003: rdp never from internet
deny[msg] {
  rc := input.resource_changes[_]
  rc.type == "aws_security_group"
  ingress := rc.change.after.ingress[_]
  ingress.from_port <= 3389
  ingress.to_port >= 3389
  cidr := ingress.cidr_blocks[_]
  cidr == "0.0.0.0/0"
  msg := sprintf("[SG-003] '%s': rdp open to internet", [rc.address])
}

# s3-001: block_public_acls must be true
deny[msg] {
  rc := input.resource_changes[_]
  rc.type == "aws_s3_bucket_public_access_block"
  rc.change.after.block_public_acls == false
  msg := sprintf("[S3-001] '%s': block_public_acls must be true", [rc.address])
}

# s3-002: block_public_policy must be true
deny[msg] {
  rc := input.resource_changes[_]
  rc.type == "aws_s3_bucket_public_access_block"
  rc.change.after.block_public_policy == false
  msg := sprintf("[S3-002] '%s': block_public_policy must be true", [rc.address])
}

# enc-001: ebs volumes must be encrypted
deny[msg] {
  rc := input.resource_changes[_]
  rc.type == "aws_ebs_volume"
  rc.change.after.encrypted == false
  msg := sprintf("[ENC-001] '%s': ebs volume not encrypted", [rc.address])
}

# rds-001: rds must not be publicly accessible
deny[msg] {
  rc := input.resource_changes[_]
  rc.type == "aws_db_instance"
  rc.change.after.publicly_accessible == true
  msg := sprintf("[RDS-001] '%s': rds instance is publicly accessible", [rc.address])
}

# nfw-001: network firewall delete protection required outside dev
deny[msg] {
  rc := input.resource_changes[_]
  rc.type == "aws_networkfirewall_firewall"
  rc.change.after.tags.Environment != "dev"
  rc.change.after.delete_protection == false
  msg := sprintf("[NFW-001] '%s': delete_protection must be enabled in non-dev environments", [rc.address])
}
