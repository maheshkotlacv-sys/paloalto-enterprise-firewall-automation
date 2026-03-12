# ties the three modules together
# if you change vpc/subnet IDs update tfvars.example too
# cross-module outputs kept explicit here - easier to trace deps

module "bootstrap_s3" {
  source = "./modules/bootstrap_s3"

  name_prefix        = local.name_prefix
  bootstrap_xml_path = var.bootstrap_xml_path
  tags               = local.common_tags
}

module "security_groups" {
  source = "./modules/security_groups"

  name_prefix        = local.name_prefix
  vpc_id             = var.vpc_id
  allowed_mgmt_cidrs = var.allowed_mgmt_cidrs
  tags               = local.common_tags
}

module "vm_series_primary" {
  source = "./modules/vm_series"

  name_prefix            = "${local.name_prefix}-primary"
  ami_id                 = var.vm_series_ami
  instance_type          = var.vm_series_instance_type
  key_pair_name          = var.key_pair_name
  availability_zone      = var.vm_series_primary_az
  mgmt_subnet_id         = var.mgmt_subnet_id
  untrust_subnet_id      = var.untrust_subnet_id
  trust_subnet_id        = var.trust_subnet_id
  ha_subnet_id           = var.ha_subnet_id
  mgmt_security_group_id = module.security_groups.mgmt_sg_id
  data_security_group_id = module.security_groups.data_sg_id
  ha_security_group_id   = module.security_groups.ha_sg_id
  bootstrap_s3_bucket    = module.bootstrap_s3.bucket_name
  bootstrap_iam_role_arn = module.bootstrap_s3.iam_instance_profile_arn
  ha_role                = "primary"
  tags                   = local.common_tags
}

module "vm_series_secondary" {
  source = "./modules/vm_series"

  name_prefix            = "${local.name_prefix}-secondary"
  ami_id                 = var.vm_series_ami
  instance_type          = var.vm_series_instance_type
  key_pair_name          = var.key_pair_name
  availability_zone      = var.vm_series_secondary_az
  mgmt_subnet_id         = var.mgmt_subnet_id
  untrust_subnet_id      = var.untrust_subnet_id
  trust_subnet_id        = var.trust_subnet_id
  ha_subnet_id           = var.ha_subnet_id
  mgmt_security_group_id = module.security_groups.mgmt_sg_id
  data_security_group_id = module.security_groups.data_sg_id
  ha_security_group_id   = module.security_groups.ha_sg_id
  bootstrap_s3_bucket    = module.bootstrap_s3.bucket_name
  bootstrap_iam_role_arn = module.bootstrap_s3.iam_instance_profile_arn
  ha_role                = "secondary"
  tags                   = local.common_tags
}

# only deploy cgw if vpn_peer_ip set, leave empty in dev
resource "aws_customer_gateway" "dc_edge" {
  count      = var.vpn_peer_ip != "" ? 1 : 0
  bgp_asn    = 65000
  ip_address = var.vpn_peer_ip
  type       = "ipsec.1"

  tags = merge(local.common_tags, {
    Name = "${local.name_prefix}-cgw-dc-edge"
  })
}
