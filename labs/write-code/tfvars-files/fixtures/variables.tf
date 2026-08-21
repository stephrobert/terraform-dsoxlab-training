variable "region" {
  type    = string
  default = "eu-west-1"
}

variable "bucket" {
  type    = string
  default = "app-defaut"
}

variable "replicas" {
  type    = number
  default = 1
}
