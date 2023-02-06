terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      # version = "~> 3.65"
    }
  }

  required_version = ">= 1.0"
}

provider "aws" {
  region = "eu-west-3"


  default_tags {
    tags = {
      Name        = "${var.name}-${var.coog_main_version}-${var.ci_pipeline_id}"
      Owner       = "coopengo"
      Managed_by  = "ec2-instance-gitlab_runner-manager"
      Environment = "production"
      Project     = lower("gitlab-cicd")
    }
  }
}
