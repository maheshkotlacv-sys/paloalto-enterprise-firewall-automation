variable "name_prefix" {
  type = string
}
variable "vpc_id" {
  type = string
}
variable "mgmt_allowed_cidrs" {
  type    = list(string)
  default = []
}
variable "tags" {
  type    = map(string)
  default = {}
}
