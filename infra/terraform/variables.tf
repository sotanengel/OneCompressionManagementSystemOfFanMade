variable "region" {
  type    = string
  default = "us-east-1"
}

variable "aws_region" {
  description = "AWS region to deploy into (alias for region)"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  type    = string
  default = "ocms"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "s3_bucket_name" {
  type = string
}

variable "vpc_id" {
  description = "VPC ID for the OCMS infrastructure"
  type        = string
  default     = ""
}

variable "private_route_table_ids" {
  description = "Route table IDs for private subnets (for S3 VPC endpoint)"
  type        = list(string)
  default     = []
}
