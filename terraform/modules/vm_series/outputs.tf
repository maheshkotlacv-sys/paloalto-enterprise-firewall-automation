output "instance_id"      { value = aws_instance.vm_series.id }
output "mgmt_public_ip"   { value = aws_eip.mgmt.public_ip }
output "untrust_eip"      { value = try(aws_eip.untrust[0].public_ip, null) }
output "trust_private_ip" { value = aws_network_interface.trust.private_ip }
