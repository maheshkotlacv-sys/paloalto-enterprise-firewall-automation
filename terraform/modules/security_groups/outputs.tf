output "mgmt_sg_id" {
  value = aws_security_group.mgmt.id
}

output "data_sg_id" {
  value = aws_security_group.data.id
}

output "ha_sg_id" {
  value = aws_security_group.ha.id
}
