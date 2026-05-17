resource "aws_key_pair" "deployer" {
  key_name   = "${module.label.namespace}-${module.label.environment}-${module.label.name}-key"
  public_key = var.public_key
}

resource "aws_instance" "app_server" {
  ami           = var.instance_image
  instance_type = var.instance_type
  subnet_id     = aws_subnet.public.id
  vpc_security_group_ids = [
    aws_security_group.api_sg.id
  ]
  key_name = aws_key_pair.deployer.key_name

  user_data = file("userdata.sh")

  root_block_device {
    volume_size           = 20
    volume_type           = "gp3"
    delete_on_termination = false
  }
}