# La version de Terraform est fournie. La contrainte du provider est a ecrire.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "???"
    }
  }
}
