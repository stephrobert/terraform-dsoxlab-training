terraform {
  required_version = ">= 1.15.0"

  required_providers {
    local  = { source = "hashicorp/local", version = "~> 2.5" }
    null   = { source = "hashicorp/null", version = "~> 3.2" }
    random = { source = "hashicorp/random", version = "~> 3.6" }
  }
}
