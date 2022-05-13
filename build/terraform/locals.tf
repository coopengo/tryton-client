locals {
  common_tags = {
    Name        = lower(var.name)
    Owner       = lower(var.owner)
    Managed_by  = lower("terraform")
    Environment = lower(var.environment)
    Project     = lower("tryton")
  }
}