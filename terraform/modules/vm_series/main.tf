# single vm-series instance with 4 ENIs
# eth0=mgmt, eth1=untrust, eth2=trust, eth3=ha
# bootstrap via s3 on first boot - takes ~8 min dont panic

# source/dest check must be off on data plane ENIs
# panos routes traffic it doesnt originate and aws will drop it otherwise
resource "aws_network_interface" "mgmt" {
  subnet_id       = var.mgmt_subnet_id
  security_groups = [var.mgmt_security_group_id]
  description     = "${var.name_prefix} mgmt"
  tags            = merge(var.tags, { Name = "${var.name_prefix}-eni-mgmt" })
}

resource "aws_network_interface" "untrust" {
  subnet_id         = var.untrust_subnet_id
  security_groups   = [var.data_security_group_id]
  source_dest_check = false
  description       = "${var.name_prefix} untrust"
  tags              = merge(var.tags, { Name = "${var.name_prefix}-eni-untrust" })
}

resource "aws_network_interface" "trust" {
  subnet_id         = var.trust_subnet_id
  security_groups   = [var.data_security_group_id]
  source_dest_check = false
  description       = "${var.name_prefix} trust"
  tags              = merge(var.tags, { Name = "${var.name_prefix}-eni-trust" })
}

resource "aws_network_interface" "ha" {
  subnet_id       = var.ha_subnet_id
  security_groups = [var.ha_security_group_id]
  description     = "${var.name_prefix} ha"
  tags            = merge(var.tags, { Name = "${var.name_prefix}-eni-ha" })
}

resource "aws_eip" "mgmt" {
  domain            = "vpc"
  network_interface = aws_network_interface.mgmt.id
  tags              = merge(var.tags, { Name = "${var.name_prefix}-eip-mgmt" })
}

# secondary doesnt get an untrust EIP - shares primary's after failover
resource "aws_eip" "untrust" {
  count             = var.ha_role == "primary" ? 1 : 0
  domain            = "vpc"
  network_interface = aws_network_interface.untrust.id
  tags              = merge(var.tags, { Name = "${var.name_prefix}-eip-untrust" })
}

resource "aws_instance" "vm_series" {
  ami               = var.ami_id
  instance_type     = var.instance_type
  availability_zone = var.availability_zone
  key_name          = var.key_pair_name

  iam_instance_profile = var.bootstrap_iam_role_arn

  # eth0 must be device_index 0 - panos expects mgmt first for bootstrap
  network_interface {
    network_interface_id = aws_network_interface.mgmt.id
    device_index         = 0
  }
  network_interface {
    network_interface_id = aws_network_interface.untrust.id
    device_index         = 1
  }
  network_interface {
    network_interface_id = aws_network_interface.trust.id
    device_index         = 2
  }
  network_interface {
    network_interface_id = aws_network_interface.ha.id
    device_index         = 3
  }

  # tells panos which s3 bucket has bootstrap config
  user_data = base64encode(<<-BOOTSTRAP
    vmseries-bootstrap-aws-s3bucket=${var.bootstrap_s3_bucket}
  BOOTSTRAP
  )

  root_block_device {
    volume_type = "gp3"
    volume_size = 60
    encrypted   = true
  }

  tags = merge(var.tags, {
    Name   = "${var.name_prefix}-vm-series"
    HaRole = var.ha_role
  })

  # dont let terraform replace instance on ami/userdata changes
  # panos upgrades go through the device, not terraform
  lifecycle {
    ignore_changes = [user_data, ami]
  }
}
