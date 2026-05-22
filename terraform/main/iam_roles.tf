resource "aws_iam_role" "ec2_role" {
  name = "${var.namespace}-${var.environment}-${var.name}-ecr-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = {
        Service = "ec2.amazonaws.com"
      }
    }]
  })
}

resource "aws_iam_role_policy_attachment" "ecr" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryReadOnly"
}

# Required for SSM Session Manager and ssm send-command — allows GitHub Actions
# to run deploy commands on EC2 without opening port 22
resource "aws_iam_role_policy_attachment" "ssm_core" {
  role       = aws_iam_role.ec2_role.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore"
}

resource "aws_iam_role_policy" "ssm-policy" {
  role = aws_iam_role.ec2_role.name
  name = "${var.namespace}-${var.environment}-${var.name}-ssm-policy"
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "ssm:GetParameters",
          "ssm:GetParameter",
          "ssm:GetParametersByPath"
        ]
        # Path matches the SSM prefix: /${var.namespace}-${var.environment}-${var.name}/
        # e.g. /skillbae-staging-api/* or /skillbae-prod-api/*
        Resource = "arn:aws:ssm:${var.aws_region}:*:parameter/${var.namespace}-${var.environment}-${var.name}/*"
      },
      {
        Sid    = "KMSDecrypt"
        Effect = "Allow"
        Action = "kms:Decrypt"
        # KMS decrypt needed for SecureString parameters
        # * is required here — KMS key ARNs are not known until key is used
        Resource = "*"
      }
    ]
  })
}
resource "aws_iam_instance_profile" "ec2" {
  name = "${var.namespace}-${var.environment}-${var.name}-ec2-profile"
  role = aws_iam_role.ec2_role.name
}
