# Fourni, complet. A ne pas modifier.
#
# Le provider vise l'emulateur local Floci : aucun compte AWS, aucune facture.
# Les trois `skip_*` empechent le provider d'appeler le vrai AWS pour valider
# des identifiants qui n'en sont pas.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

variable "emulateur_endpoint" {
  description = "Ou joindre Floci."
  type        = string
  default     = "http://localhost:14566"
}

provider "aws" {
  region     = "eu-west-3"
  access_key = "test"
  secret_key = "test"

  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true

  s3_use_path_style = true

  endpoints {
    ec2 = var.emulateur_endpoint
    s3  = var.emulateur_endpoint
  }
}
