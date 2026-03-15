# mgmt sg - only approved CIDRs, no 0.0.0.0/0 ever
# 443=web ui, 22=cli, 3978=panorama log collection
# add new ranges to allowed_mgmt_cidrs var, not here
resource "aws_security_group" "mgmt" {
  name        = "${var.name_prefix}-sg-mgmt"
  description = "vm-series mgmt - approved CIDRs only"
  vpc_id      = var.vpc_id

  ingress {
    description = "https web ui"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = var.allowed_mgmt_cidrs
  }

  ingress {
    description = "ssh"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = var.allowed_mgmt_cidrs
  }

  ingress {
    description = "panorama log collection"
    from_port   = 3978
    to_port     = 3978
    protocol    = "tcp"
    cidr_blocks = var.allowed_mgmt_cidrs
  }

  ingress {
    description = "icmp from mgmt nets"
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    cidr_blocks = var.allowed_mgmt_cidrs
  }

  # outbound needed for license activation + content updates
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-sg-mgmt" })
}

# data plane sg - allow all inbound, panos enforces policy not aws
# dont put deny rules here, it breaks asymmetric flows through the firewall
resource "aws_security_group" "data" {
  name        = "${var.name_prefix}-sg-data"
  description = "vm-series data plane - panos does the blocking"
  vpc_id      = var.vpc_id

  ingress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-sg-data" })
}

# ha sg - self-referencing only, peers talk to each other
# 28769=HA1 heartbeat+config sync, 28260=HA2 session sync
resource "aws_security_group" "ha" {
  name        = "${var.name_prefix}-sg-ha"
  description = "vm-series ha - peer comms only"
  vpc_id      = var.vpc_id

  ingress {
    description = "HA1 config sync"
    from_port   = 28769
    to_port     = 28769
    protocol    = "tcp"
    self        = true
  }

  ingress {
    description = "HA2 session sync"
    from_port   = 28260
    to_port     = 28260
    protocol    = "tcp"
    self        = true
  }

  ingress {
    description = "icmp between ha peers"
    from_port   = -1
    to_port     = -1
    protocol    = "icmp"
    self        = true
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }

  tags = merge(var.tags, { Name = "${var.name_prefix}-sg-ha" })
}
