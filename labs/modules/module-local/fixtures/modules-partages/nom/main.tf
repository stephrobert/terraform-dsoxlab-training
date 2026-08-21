# Module partage : compose un nom, avec ou sans suffixe aleatoire.
# CE MODULE EST COMPLET, ne pas le modifier.

terraform {
  required_providers {
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

variable "base" {
  description = "Base du nom a composer."
  type        = string
}

variable "suffixe_aleatoire" {
  description = "Ajoute un suffixe aleatoire au nom compose."
  type        = bool
  default     = true
}

resource "random_pet" "suffixe" {
  count  = var.suffixe_aleatoire ? 1 : 0
  length = 1
}

output "complet" {
  description = "Nom compose, suffixe compris s'il est demande."
  value       = var.suffixe_aleatoire ? "${var.base}-${random_pet.suffixe[0].id}" : var.base
}
