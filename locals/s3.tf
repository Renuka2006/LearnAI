locals {
  project = "bucket-using-locals"
  project_owner = "Renu"
  bucket = "test_bucket"
}
locals {
  common_tags = {
  cost_center = "Own"
  project_owner = local.project_owner

  }
}

resource "random_id" "s3_random_id" {
  byte_length = 5
}

resource "aws_s3_bucket" "local_S3" {

  bucket = "${local.project}-${random_id.s3_random_id.hex}"
  tags = merge(local.common_tags,{
    Name = "hello"
    project = local.project
  })
  lifecycle {
    create_before_destroy = true
  }
}