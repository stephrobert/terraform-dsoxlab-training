# La configuration racine du SOCLE : ce qui a un cycle de vie long, et ce que
# d'autres configurations consomment.
#
# Elle ne connait aucun workspace : la separation se fait ici par CONFIGURATION,
# chacune avec son propre etat.

terraform {
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

variable "cidr" {
  description = "Plage reseau servie par ce socle."
  type        = string
  default     = "10.1.0.0/24"
}

resource "random_pet" "reseau" {
  length = 2

  # L'identifiant du reseau est refait des que la plage change : deux plages
  # differentes ne peuvent pas porter le meme identifiant.
  keepers = {
    cidr = var.cidr
  }
}

resource "local_file" "reseau" {
  filename = "${path.root}/produits/reseau.conf"
  content  = "reseau ${random_pet.reseau.id} cidr ${var.cidr}\n"
}

# Ces deux sorties sont le CONTRAT du socle : c'est tout ce qu'une autre
# configuration pourra lire. Rien d'autre ne traverse la frontiere.

output "identifiant_socle" {
  description = "Identifiant du reseau produit par ce socle."
  value       = ???
}

output "cidr_reseau" {
  description = "Plage reseau servie."
  value       = ???
}
