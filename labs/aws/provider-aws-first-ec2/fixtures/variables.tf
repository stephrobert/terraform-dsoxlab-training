variable "aws_region" {
  description = "Region visee. L'emulateur l'accepte telle quelle."
  type        = string
  default     = "eu-west-3"
}

variable "ami_id" {
  description = "AMI demandee. L'emulateur l'ignore et retombe sur son image de base."
  type        = string
  default     = "ami-0abcdef1234567890"
}

variable "instance_type" {
  description = "Gabarit de l'instance."
  type        = string
  default     = "t3.micro"
}

variable "floci_endpoint" {
  description = "Adresse de l'API locale qui remplace AWS."
  type        = string
  default     = "http://localhost:14566"
}

variable "common_tags" {
  description = "Tags que TOUTE ressource de cette racine doit porter."
  type        = map(string)

  default = {
    projet      = "lab-terraform"
    environnement = "formation"
    gestion     = "terraform"
  }
}
