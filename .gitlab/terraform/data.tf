data "aws_security_groups" "gitlab_runner_slave" {
  filter {
    name   = "group-name"
    values = ["gitlab_runner-slave"]
  }

  filter {
    name   = "vpc-id"
    values = [var.vpc_id]
  }
}

data "aws_ami" "windows" {
  most_recent = true
  owners      = ["self"]
  filter {
    name   = "name"
    values = ["gtk-build-python3_*"]
  }

  filter {
    name   = "platform"
    values = ["windows"]
  }
}

data "aws_subnet" "gitlab_runner" {
  availability_zone = var.availability_zone
  vpc_id = var.vpc_id

  tags = {
    Type = "public subnets"
  }
}