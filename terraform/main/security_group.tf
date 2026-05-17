resource "aws_security_group" "api_sg" {
  name        = "${module.label.namespace}-${module.label.environment}-${module.label.name}-api-sg"
  vpc_id      = aws_vpc.main.id
  description = "Security group for SkillBae backend EC2"

  ingress {
    description = "SSH from admin"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["49.43.161.113/32"]
  }

  ingress {
    description = "HTTP traffic"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    description = "Outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
  tags = {
    Name = "${module.label.namespace}-${module.label.environment}-${module.label.name}-api-sg"
  }
}