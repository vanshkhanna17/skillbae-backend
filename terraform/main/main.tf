provider "aws" {
  region = var.aws_region
}

terraform {
  required_version = ">=1.6.0"

  required_providers {
    aws = {
        source = "hashicorp/aws"
        version = "5.26.0"
    }
  }

  backend "s3" {
    region = var.aws_region
    encrypt = "true"
  }
}

module "label" {
  source      = "git::https://github.com/cloudposse/terraform-null-label.git?ref=tags/0.21.0"

  namespace   = var.namespace
  environment = var.environment
  name        = var.name

  delimiter           = var.delimiter
  regex_replace_chars = var.regex_replace_chars
  tags                = var.tags
}