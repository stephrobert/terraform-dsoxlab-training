terraform {
  required_version = ">= 1.15.0"

  required_providers {
    local  = { source = "hashicorp/local", version = "~> 2.5" }
    # random 3.7+ pour la ressource ephemere random_password.
    random = { source = "hashicorp/random", version = ">= 3.7.0" }
  }
}
