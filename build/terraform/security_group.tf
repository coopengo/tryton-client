resource "aws_security_group" "postgres_sql" {
  name        = "tryton-${var.coog_main_version}-${var.ci_pipeline_id}"
  description = "Build tryton-${var.coog_main_version} for the Gitlab pipeline ${var.ci_pipeline_id}"
  vpc_id      = var.vpc_id

  // allow traffic for TCP 22 from gitlab_runner_slave
  ingress {
    from_port       = 22
    to_port         = 22
    protocol        = "tcp"
    security_groups = data.aws_security_groups.gitlab_runner_slave.ids
  }

  // outbound internet access
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { for k, v in local.common_tags : k => v if k != "Name" }
}