provider "aws" {
  region = var.aws_region

  # slap these on everything so we dont forget to tag resources manually
  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "terraform"
      Owner       = "network-security-team"
      Repository  = "paloalto-enterprise-firewall-automation"
    }
  }
}

# panos provider for bootstrap validation and seeding address objects
# dont hardcode creds - use env vars:
#   export PANOS_HOSTNAME=...
#   export PANOS_USERNAME=...
#   export PANOS_PASSWORD=...
provider "panos" {
  hostname = var.panorama_hostname
  username = var.panorama_username
  password = var.panorama_password
}
