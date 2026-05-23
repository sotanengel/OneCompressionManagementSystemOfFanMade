output "security_group_id" {
  value = aws_security_group.ec2.id
}

output "iam_role_name" {
  value = aws_iam_role.ec2.name
}

output "instance_profile_name" {
  value = aws_iam_instance_profile.ec2.name
}
