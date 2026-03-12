variable "name_prefix"            { type = string }
variable "instance_count"         { type = number; default = 2 }
variable "instance_type"          { type = string }
variable "panos_version"          { type = string }
variable "key_pair_name"          { type = string }
variable "mgmt_subnet_id"         { type = string }
variable "untrust_subnet_id"      { type = string }
variable "trust_subnet_id"        { type = string }
variable "ha_subnet_id"           { type = string; default = "" }
variable "mgmt_sg_id"             { type = string }
variable "untrust_sg_id"          { type = string }
variable "trust_sg_id"            { type = string }
variable "bootstrap_bucket_name"  { type = string }
variable "bootstrap_iam_role_arn" { type = string }
variable "tags"                   { type = map(string); default = {} }
