output "bucket_name"    { value = aws_s3_bucket.bootstrap.bucket }
output "bucket_arn"     { value = aws_s3_bucket.bootstrap.arn }
output "iam_role_arn"   { value = aws_iam_role.bootstrap.arn }
output "instance_profile_name" { value = aws_iam_instance_profile.bootstrap.name }
