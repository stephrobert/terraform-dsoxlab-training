# Fourni, deja correct. Aucun provider distant : le lab tourne partout ou
# `terraform` est sur le PATH, sans reseau.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
