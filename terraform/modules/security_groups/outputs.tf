output "mgmt_sg_id"    { value = aws_security_group.mgmt.id }
output "untrust_sg_id" { value = aws_security_group.untrust.id }
output "trust_sg_id"   { value = aws_security_group.trust.id }
