# ─────────────────────────────────────────────────────────────────────────────
# SSM Parameter Store — SkillBae Staging Environment Variables
#
# Naming convention: /skillbae/staging/<VAR_NAME>
#   - Lets EC2 fetch ALL staging params in one API call using get-parameters-by-path
#   - Easy to add /skillbae/prod/<VAR_NAME> later without any conflicts
#
# Two types:
#   String       → non-sensitive config, stored in plaintext
#   SecureString → sensitive secrets, encrypted at rest by AWS KMS (free tier)
# ─────────────────────────────────────────────────────────────────────────────

locals {
  ssm_prefix = "/${var.namespace}-${var.environment}-${var.name}"
}

# ─── Non-Sensitive Config (String) ───────────────────────────────────────────

resource "aws_ssm_parameter" "app_name" {
  name  = "${local.ssm_prefix}/APP_NAME"
  type  = "String"
  value = "SkillBae API"
}

resource "aws_ssm_parameter" "app_description" {
  name  = "${local.ssm_prefix}/APP_DESCRIPTION"
  type  = "String"
  value = "Backend API for SkillBae"
}

resource "aws_ssm_parameter" "app_version" {
  name  = "${local.ssm_prefix}/APP_VERSION"
  type  = "String"
  value = "1.0.0"
}

resource "aws_ssm_parameter" "environment" {
  name  = "${local.ssm_prefix}/ENVIRONMENT"
  type  = "String"
  value = var.environment # "staging" — comes from staging.tfvars
}

resource "aws_ssm_parameter" "debug" {
  name  = "${local.ssm_prefix}/DEBUG"
  type  = "String"
  value = "False" # MUST be False on any deployed environment
}

resource "aws_ssm_parameter" "algorithm" {
  name  = "${local.ssm_prefix}/ALGORITHM"
  type  = "String"
  value = "HS256"
}

resource "aws_ssm_parameter" "access_token_expire_minutes" {
  name  = "${local.ssm_prefix}/ACCESS_TOKEN_EXPIRE_MINUTES"
  type  = "String"
  value = "30"
}

resource "aws_ssm_parameter" "refresh_token_expire_days" {
  name  = "${local.ssm_prefix}/REFRESH_TOKEN_EXPIRE_DAYS"
  type  = "String"
  value = "7"
}

resource "aws_ssm_parameter" "cookie_secure" {
  name  = "${local.ssm_prefix}/COOKIE_SECURE"
  type  = "String"
  value = "False" # HTTP only for staging — set True when HTTPS is added
}

resource "aws_ssm_parameter" "cookie_samesite" {
  name  = "${local.ssm_prefix}/COOKIE_SAMESITE"
  type  = "String"
  value = "Lax"
}

resource "aws_ssm_parameter" "cookie_path" {
  name  = "${local.ssm_prefix}/COOKIE_PATH"
  type  = "String"
  value = "/"
}

resource "aws_ssm_parameter" "cookie_domain" {
  name  = "${local.ssm_prefix}/COOKIE_DOMAIN"
  type  = "String"
  value = "none" # SSM requires non-empty; app treats "none" as unset → browser defaults to current host
}

resource "aws_ssm_parameter" "cors_origins" {
  name  = "${local.ssm_prefix}/BACKEND_CORS_ORIGINS"
  type  = "String"
  value = aws_cloudfront_distribution.api_cdn.domain_name # passed via staging.tfvars — e.g. "http://<EC2-IP>"
}

# ─── Database Config (String — not secret, host/db name are not sensitive) ───

resource "aws_ssm_parameter" "postgres_user" {
  name  = "${local.ssm_prefix}/POSTGRES_USER"
  type  = "String"
  value = "skillbae_admin"
}

resource "aws_ssm_parameter" "postgres_db" {
  name  = "${local.ssm_prefix}/POSTGRES_DB"
  type  = "String"
  value = "skillbae"
}

# ─── Sensitive Secrets (SecureString — encrypted by AWS KMS) ─────────────────

resource "aws_ssm_parameter" "postgres_password" {
  name  = "${local.ssm_prefix}/POSTGRES_PASSWORD"
  type  = "SecureString"
  value = var.postgres_password # passed via staging.tfvars, never hardcoded
}

resource "aws_ssm_parameter" "database_url" {
  name = "${local.ssm_prefix}/DATABASE_URL"
  type = "SecureString"
  # Uses postgres service name — works because both containers are on same Docker network
  value = "postgresql+asyncpg://skillbae_admin:${var.postgres_password}@postgres:5432/skillbae"
}

resource "aws_ssm_parameter" "database_sync_url" {
  name  = "${local.ssm_prefix}/DATABASE_SYNC_URL"
  type  = "SecureString"
  value = "postgresql+psycopg://skillbae_admin:${var.postgres_password}@postgres:5432/skillbae"
}

resource "aws_ssm_parameter" "secret_key" {
  name  = "${local.ssm_prefix}/SECRET_KEY"
  type  = "SecureString"
  value = var.secret_key # generate with: openssl rand -hex 64
}

resource "aws_ssm_parameter" "refresh_token_secret_key" {
  name  = "${local.ssm_prefix}/REFRESH_TOKEN_SECRET_KEY"
  type  = "SecureString"
  value = var.refresh_token_secret_key # different from SECRET_KEY — generate separately
}
