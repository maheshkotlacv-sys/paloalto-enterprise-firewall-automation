variable "name_prefix" {
  type = string
}

variable "ami_id" {
  type = string
}

variable "instance_type" {
  type = string
}

variable "key_pair_name" {
  type = string
}

variable "availability_zone" {
  type = string
}

variable "mgmt_subnet_id" {
  type = string
}

variable "untrust_subnet_id" {
  type = string
}

variable "trust_subnet_id" {
  type = string
}

variable "ha_subnet_id" {
  type    = string
  default = ""
}

variable "mgmt_security_group_id" {
  type = string
}

variable "data_security_group_id" {
  type = string
}

variable "ha_security_group_id" {
  type = string
}

variable "bootstrap_s3_bucket" {
  type = string
}

variable "bootstrap_iam_role_arn" {
  type = string
}

variable "ha_role" {
  type    = string
  default = "primary"
}

variable "tags" {
  type    = map(string)
  default = {}
}
