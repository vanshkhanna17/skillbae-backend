variable "aws_region" {
  type    = string
  default = "ap-south-1"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "public_subnet_cidr" {
  type    = string
  default = "10.0.1.0/24"
}

variable "instance_type" {
  type    = string
  default = "t4g.micro"
}

variable "instance_image" {
  type        = string
  default     = "ami-0fa0340d4a8bdd6ee"
  description = "EC2 instance AMI"
}

variable "delimiter" {
  type        = string
  default     = "-"
  description = "Delimiter to be used between `namespace`, `environment`, `stage`, `name` and `attributes`"
}

variable "regex_replace_chars" {
  type        = string
  default     = "/[^a-zA-Z0-9-.]/"
  description = "Regex to replace chars with empty string in `namespace`, `environment`, `stage` and `name`. By default only hyphens, letters and digits are allowed, all other chars are removed"
}

variable "namespace" {
  type        = string
  default     = ""
  description = "Namespace, which could be your organization name or abbreviation, e.g. 'skillbae'"
}

variable "environment" {
  type        = string
  default     = ""
  description = "Environment, e.g. 'staging' or 'prod'"
}

variable "name" {
  type        = string
  default     = ""
  description = "Solution name, e.g. 'app' or 'api'"
}

variable "tags" {
  type        = map(string)
  default     = {}
  description = "Additional tags (e.g. `map('BusinessUnit','XYZ')`"
}

variable "public_key" {
  type        = string
  description = "SSH public key for EC2 key pair"
}

variable "postgres_password" {
  type        = string
  sensitive   = true # marks as sensitive — Terraform won't print it in plan/apply output
  description = "Postgres database password. Generate with: openssl rand -hex 32"
}

variable "secret_key" {
  type        = string
  sensitive   = true
  description = "JWT signing secret. Generate with: openssl rand -hex 64"
}

variable "refresh_token_secret_key" {
  type        = string
  sensitive   = true
  description = "JWT refresh token secret. Generate with: openssl rand -hex 64 (must differ from secret_key)"
}

variable "cors_origins" {
  type        = string
  description = "Comma-separated CORS origins. e.g. http://<EC2-IP> for staging"
}
