# Fourni. A NE PAS MODIFIER.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}
