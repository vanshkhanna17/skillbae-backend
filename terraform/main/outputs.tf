output "ec2_public_ip" {
  value = aws_instance.app_server.public_ip
}

output "ec2_public_dns" {
  value = aws_instance.app_server.public_dns
}

output "ecr_repository_url" {
  value = aws_ecr_repository.app_repo.repository_url
}
