output "instance_ids"     { value = aws_instance.vmseries[*].id }
output "mgmt_public_ips"  { value = aws_eip.mgmt[*].public_ip }
output "untrust_eips"     { value = aws_eip.untrust[*].public_ip }
output "trust_private_ips" { value = aws_network_interface.trust[*].private_ip }
