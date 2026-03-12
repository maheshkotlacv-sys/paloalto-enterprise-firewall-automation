variable "name_prefix" { type = string }
variable "bucket_name" { type = string }
variable "init_cfg"    { type = string; description = "Rendered init-cfg.txt content" }
variable "tags"        { type = map(string); default = {} }
