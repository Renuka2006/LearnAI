output "Bucket_name" {
  value = aws_s3_bucket.local_S3.bucket
  sensitive = true #does not show the value
}