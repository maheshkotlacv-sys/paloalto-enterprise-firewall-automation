locals {
  name_prefix = "${var.project_name}-${var.environment}"

  # panos needs these exact folder names in s3 bootstrap bucket
  bootstrap_prefixes = ["config/", "license/", "software/", "content/"]

  # eth0=mgmt, eth1=untrust, eth2=trust, eth3=ha
  # mgmt must be device_index 0 or bootstrap wont find the bucket
  interface_map = {
    mgmt    = 0
    untrust = 1
    trust   = 2
    ha      = 3
  }

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "terraform"
  }
}
