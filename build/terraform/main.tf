# To do: 
# - Intégrer une deuxieme base de données pour les tests pypy
# - Revoir la structure du terraform pour mettre les bases coog et coog-pypy dans un même fichier

# spot_price - (Optional; Default: On-demand price) The maximum price to request on the spot market.
module "asg_gitlab_runner_manager" {
  source  = "terraform-aws-modules/autoscaling/aws"
  version = "~> 4.4"

  name = "${var.name}-${var.coog_main_version}-${var.ci_pipeline_id}"

  min_size                  = 1
  max_size                  = 1
  desired_capacity          = 1
  wait_for_capacity_timeout = 0
  health_check_type         = "EC2"
  vpc_zone_identifier       = [data.aws_subnet.gitlab_runner.id]

  key_name         = "gitlab-ci"
  # user_data_base64 = filebase64("configure_postgres.sh")

  # Launch template
  create_lt = true

  image_id                   = data.aws_ami.windows.image_id
  instance_type              = var.instance_type
  ebs_optimized              = false
  enable_monitoring          = false
  use_mixed_instances_policy = true

  mixed_instances_policy = {
    instances_distribution = {
      on_demand_base_capacity                  = 0
      on_demand_percentage_above_base_capacity = 0
      spot_allocation_strategy                 = "capacity-optimized"
    }
    override = [

      {
        instance_type     = "t3.medium"
        weighted_capacity = "5"
      },
      {
        instance_type     = "c6i.large"
        weighted_capacity = "4"
      },
      {
        instance_type     = "c5n.large"
        weighted_capacity = "3"
      },
      {
        instance_type     = "c5a.large"
        weighted_capacity = "2"
      },
      {
        instance_type     = "c5.large"
        weighted_capacity = "1"
      },
    ]
  }

  block_device_mappings = [
    {
      # Root volume
      device_name = "/dev/sda1"
      no_device   = 0
      ebs = {
        delete_on_termination = true
        encrypted             = false
        volume_size           = 50
        volume_type           = "gp3"
      }
    }
  ]

  credit_specification = {
    cpu_credits = "standard"
  }

  network_interfaces = [
    {
      delete_on_termination       = true
      description                 = "eth0"
      associate_public_ip_address = true
      device_index                = 0
      security_groups             = [aws_security_group.postgres_sql.id]
    }
  ]

  tags_as_map = { for k, v in local.common_tags : k => v if k != "Name" }
}