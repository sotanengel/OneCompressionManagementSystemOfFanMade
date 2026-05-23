output "hf_token_secret_arn" {
  value = aws_secretsmanager_secret.hf_token.arn
}

output "db_password_secret_arn" {
  value = aws_secretsmanager_secret.db_password.arn
}
