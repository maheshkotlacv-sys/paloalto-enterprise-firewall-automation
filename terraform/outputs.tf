output "vm_series_mgmt_ips" {
  description = "Public management IP addresses of VM-Series instances."
  value       = module.vm_series.mgmt_public_ips
}

output "vm_series_instance_ids" {
  description = "EC2 instance IDs of VM-Series instances."
  value       = module.vm_series.instance_ids
}

output "vm_series_trust_ips" {
  description = "Private trust interface IPs (internal facing)."
  value       = module.vm_series.trust_private_ips
}

output "vm_series_untrust_ips" {
  description = "Public/EIP addresses on untrust interface."
  value       = module.vm_series.untrust_eips
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
