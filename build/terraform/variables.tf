variable "name" {
  description = "Name to be used on all the resources as identifier"
  type        = string
  default     = "tryton"
}

variable "owner" {
  description = "Define who is the owner of theses resources"
  type        = string
  default     = "coopengo"
}

variable "environment" {
  description = "Define envionment usage"
  type        = string
  default     = "production"
}

variable "coog_main_version" {
  description = "Environnement for specific coog version test"
  type        = string
  default     = "master"
}

variable "ci_pipeline_id" {
  description = "Pipeline ID from GitLab"
  type        = string
  default     = ""
}

variable "instance_count" {
  default = "1"
}

variable "instance_tags" {
  type    = list(any)
  default = ["tryton"]
}

variable "instance_type" {
  description = "AWS instance type for postgres database"
  type        = string
  default     = "t3a.medium"
}

variable "vpc_id" {
  description = "Get AWS ID from Gitlab-runner."
  type        = string
  default     = null
}

variable "availability_zone" {
  description = "Get AWS availability_zone from Gitlab-runner. Configured on the same AZ to avoid extra billing."
  type        = string
  default     = null
}