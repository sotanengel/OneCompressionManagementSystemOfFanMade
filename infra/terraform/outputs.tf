output "vpc_id" {
  value = module.vpc.vpc_id
}

output "ec2_security_group_id" {
  value = module.ec2.security_group_id
}

output "ec2_instance_profile_name" {
  value = module.ec2.instance_profile_name
}

output "cognito_user_pool_id" {
  value = ""
}
