variable "name_prefix" {
  type = string
}

variable "bootstrap_xml_path" {
  type    = string
  default = ""
}

variable "tags" {
  type    = map(string)
  default = {}
}
