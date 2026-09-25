# Fourni, complet. Aucun compte HCP Terraform : tout se simule en local.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}
