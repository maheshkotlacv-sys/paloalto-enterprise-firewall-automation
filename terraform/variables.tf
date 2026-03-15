variable "project_name" {
  type        = string
  description = "prefix for all resource names"
  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "lowercase alphanumeric + hyphens only"
  }
}

variable "environment" {
  type        = string
  description = "dev, staging, or prod"
  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "must be dev, staging, or prod"
  }
}

variable "aws_region" {
  type        = string
  description = "aws region for vm-series"
  default     = "us-east-1"
}

variable "vpc_id" {
  type        = string
  description = "vpc where vm-series instances will live"
}

variable "mgmt_subnet_id" {
  type        = string
  description = "subnet for eth0 (management)"
}

variable "untrust_subnet_id" {
  type        = string
  description = "subnet for eth1 (untrust / WAN)"
}

variable "trust_subnet_id" {
  type        = string
  description = "subnet for eth2 (trust / LAN)"
}

variable "ha_subnet_id" {
  type        = string
  description = "subnet for eth3 (HA link)"
}

variable "vm_series_ami" {
  type        = string
  description = "ami id for pa vm-series - get from aws marketplace for your panos version"
}

variable "vm_series_instance_type" {
  type        = string
  description = "instance type - m5.xlarge is minimum, m5.2xlarge for prod"
  default     = "m5.2xlarge"
  validation {
    condition     = contains(["m5.xlarge", "m5.2xlarge", "m5.4xlarge", "c5.2xlarge", "c5.4xlarge"], var.vm_series_instance_type)
    error_message = "must be a supported vm-series instance type"
  }
}

variable "key_pair_name" {
  type        = string
  description = "ec2 key pair for initial ssh access during bootstrap"
}

variable "allowed_mgmt_cidrs" {
  type        = list(string)
  description = "cidrs allowed to reach management interface - jump host or panorama IPs only"
  validation {
    condition     = length(var.allowed_mgmt_cidrs) > 0
    error_message = "need at least one mgmt cidr"
  }
}

variable "panorama_hostname" {
  type        = string
  description = "panorama ip or fqdn"
  default     = ""
  sensitive   = true
}

variable "panorama_username" {
  type        = string
  description = "panorama api username"
  default     = ""
  sensitive   = true
}

variable "panorama_password" {
  type        = string
  description = "panorama api password - use TF_VAR_panorama_password env var in ci"
  default     = ""
  sensitive   = true
}

variable "bootstrap_xml_path" {
  type        = string
  description = "local path to bootstrap.xml to upload to s3"
  default     = "../bootstrap/config/bootstrap.xml"
}

variable "vm_series_primary_az" {
  type        = string
  description = "az for primary vm-series"
  default     = "us-east-1a"
}

variable "vm_series_secondary_az" {
  type        = string
  description = "az for secondary (ha peer)"
  default     = "us-east-1b"
}

variable "vpn_peer_ip" {
  type        = string
  description = "public ip of dc edge firewall - leave empty to skip cgw creation"
  default     = ""
}

variable "vpn_psk" {
  type        = string
  description = "pre-shared key for dc-to-aws vpn - use secrets manager in prod"
  default     = ""
  sensitive   = true
}
