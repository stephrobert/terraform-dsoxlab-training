# Fourni, complet.

variable "aws_region" {
  type    = string
  default = "eu-west-3"
}

variable "emulateur_endpoint" {
  description = "API locale qui remplace AWS."
  type        = string
  default     = "http://localhost:14566"
}

variable "bucket_nom" {
  description = "Le bucket que le role doit pouvoir lire."
  type        = string
  default     = "donnees-applicatives"
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
