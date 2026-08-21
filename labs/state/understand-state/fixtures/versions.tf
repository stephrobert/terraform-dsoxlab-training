terraform {
  # Les blocs import (import { to = ... id = ... }) datent de Terraform 1.5 et
  # s'appliquent par `terraform apply`. On exige 1.15.
  required_version = ">= 1.15.0"

  required_providers {
    random = { source = "hashicorp/random", version = ">= 3.6" }
    local  = { source = "hashicorp/local", version = ">= 2.5" }
  }
}
