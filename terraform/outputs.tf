output "primary_mgmt_ip" {
  description = "Public management IP of primary VM-Series instance."
  value       = module.vm_series_primary.mgmt_public_ip
}

output "secondary_mgmt_ip" {
  description = "Public management IP of secondary VM-Series instance."
  value       = module.vm_series_secondary.mgmt_public_ip
}

output "primary_instance_id" {
  description = "EC2 instance ID of primary VM-Series."
  value       = module.vm_series_primary.instance_id
}

output "secondary_instance_id" {
  description = "EC2 instance ID of secondary VM-Series."
  value       = module.vm_series_secondary.instance_id
}

output "primary_trust_ip" {
  description = "Private trust interface IP on primary (internal facing)."
  value       = module.vm_series_primary.trust_private_ip
}

output "primary_untrust_eip" {
  description = "Public/EIP address on primary untrust interface."
  value       = module.vm_series_primary.untrust_eip
}

output "bootstrap_bucket_name" {
  description = "S3 bootstrap bucket name."
  value       = module.bootstrap_s3.bucket_name
}

output "bootstrap_iam_role_arn" {
  description = "IAM role ARN assigned to VM-Series for S3 bootstrap access."
  value       = module.bootstrap_s3.iam_role_arn
}

output "mgmt_security_group_id" {
  description = "Security group ID controlling management interface access."
  value       = module.security_groups.mgmt_sg_id
}
