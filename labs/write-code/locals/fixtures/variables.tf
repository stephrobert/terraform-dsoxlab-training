variable "project" {
  type    = string
  default = "Atelier_Locaux"
}

variable "environment" {
  type    = string
  default = "prod"
}

variable "node_count" {
  type    = number
  default = 3
}

variable "memory_mb" {
  type    = number
  default = 2048
}

variable "db_password" {
  type      = string
  sensitive = true
  default   = "s3cr3t-lab"
}
