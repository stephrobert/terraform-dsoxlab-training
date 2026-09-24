# Fourni, a ne pas modifier.
#
# Le provider est NEUTRALISE : identifiants factices, controles desactives,
# aucun point de terminaison. Ce lab ne fait aucun appel d'API et n'applique
# rien. Tout se lit dans le PLAN, et tous les plans se lancent avec
# `-refresh=false`.
#
# Seul le premier `terraform init` a besoin du reseau, pour telecharger les
# providers.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "6.0.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.6.3"
    }
  }
}

provider "aws" {
  region     = "eu-west-3"
  access_key = "test"
  secret_key = "test"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
}
