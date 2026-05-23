resource "aws_secretsmanager_secret" "hf_token" {
  name        = "ocms/hf-token"
  description = "HuggingFace API token for model downloads"
}

resource "aws_secretsmanager_secret" "db_password" {
  name        = "ocms/db-password"
  description = "PostgreSQL database password"
}
