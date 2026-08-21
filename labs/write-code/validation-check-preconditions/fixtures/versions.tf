terraform {
  # Les blocs check datent de Terraform 1.5 ; les preconditions/postconditions
  # de 1.2 ; la validation croisee (une validation qui reference une AUTRE
  # variable) de 1.9. On exige 1.15 pour tout couvrir.
  required_version = ">= 1.15.0"

  required_providers {
    random = { source = "hashicorp/random", version = ">= 3.6" }
    local  = { source = "hashicorp/local", version = ">= 2.5" }
  }
}
