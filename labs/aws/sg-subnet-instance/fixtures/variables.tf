variable "aws_region" {
  type    = string
  default = "eu-west-3"
}

variable "emulateur_endpoint" {
  description = "API locale qui remplace AWS."
  type        = string
  default     = "http://localhost:14566"
}

variable "vpc_cidr" {
  type    = string
  default = "10.42.0.0/16"
}

variable "flux_entrants" {
  description = "Nom du flux vers le port TCP a ouvrir. TROIS entrees."
  type        = map(number)

  default = {
    ssh   = 22
    http  = 80
    https = 443
  }
}

variable "cidr_autorise" {
  description = "La seule CIDR autorisee en entree."
  type        = string
  default     = "10.42.0.0/16"
}

variable "ami_id" {
  description = "L'emulateur ignore cette valeur et retombe sur son image de base."
  type        = string
  default     = "ami-0abcdef1234567890"
}

variable "instance_type" {
  type    = string
  default = "t3.micro"
}
