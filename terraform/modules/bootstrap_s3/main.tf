# s3 bootstrap bucket for panos first-boot config
# panos reads config/ license/ software/ content/ on startup
# if bootstrap fails device comes up factory default - check s3 perms first

resource "aws_s3_bucket" "bootstrap" {
  bucket        = "${var.name_prefix}-panos-bootstrap"
  force_destroy = false
  tags          = merge(var.tags, { Name = "${var.name_prefix}-panos-bootstrap" })
}

resource "aws_s3_bucket_versioning" "bootstrap" {
  bucket = aws_s3_bucket.bootstrap.id
  versioning_configuration { status = "Enabled" }
}

resource "aws_s3_bucket_server_side_encryption_configuration" "bootstrap" {
  bucket = aws_s3_bucket.bootstrap.id
  rule {
    apply_server_side_encryption_by_default { sse_algorithm = "AES256" }
  }
}

# bootstrap bucket must never be public - contains initial device config
resource "aws_s3_bucket_public_access_block" "bootstrap" {
  bucket                  = aws_s3_bucket.bootstrap.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

# panos expects these folders to exist even if theyre empty
resource "aws_s3_object" "bootstrap_dirs" {
  for_each = toset(["config/", "license/", "software/", "content/"])
  bucket   = aws_s3_bucket.bootstrap.id
  key      = each.value
  content  = ""
}

resource "aws_s3_object" "bootstrap_xml" {
  count  = var.bootstrap_xml_path != "" ? 1 : 0
  bucket = aws_s3_bucket.bootstrap.id
  key    = "config/bootstrap.xml"
  source = var.bootstrap_xml_path
  etag   = filemd5(var.bootstrap_xml_path)
}

data "aws_iam_policy_document" "ec2_assume" {
  statement {
    effect  = "Allow"
    actions = ["sts:AssumeRole"]
    principals { type = "Service"; identifiers = ["ec2.amazonaws.com"] }
  }
}

# least priv - read only on bootstrap bucket, nothing else
data "aws_iam_policy_document" "bootstrap_read" {
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject", "s3:ListBucket"]
    resources = [aws_s3_bucket.bootstrap.arn, "${aws_s3_bucket.bootstrap.arn}/*"]
  }
}

resource "aws_iam_role" "vm_series_bootstrap" {
  name               = "${var.name_prefix}-vm-series-bootstrap-role"
  assume_role_policy = data.aws_iam_policy_document.ec2_assume.json
  tags               = var.tags
}

resource "aws_iam_role_policy" "bootstrap_read" {
  name   = "${var.name_prefix}-bootstrap-read"
  role   = aws_iam_role.vm_series_bootstrap.id
  policy = data.aws_iam_policy_document.bootstrap_read.json
}

resource "aws_iam_instance_profile" "vm_series" {
  name = "${var.name_prefix}-vm-series-profile"
  role = aws_iam_role.vm_series_bootstrap.name
  tags = var.tags
}
