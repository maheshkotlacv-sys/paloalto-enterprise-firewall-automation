output "bucket_name"            { value = aws_s3_bucket.bootstrap.bucket }
output "bucket_arn"             { value = aws_s3_bucket.bootstrap.arn }
output "iam_role_arn"           { value = aws_iam_role.vm_series_bootstrap.arn }
output "iam_instance_profile_arn" { value = aws_iam_instance_profile.vm_series.arn }
output "instance_profile_name"  { value = aws_iam_instance_profile.vm_series.name }
