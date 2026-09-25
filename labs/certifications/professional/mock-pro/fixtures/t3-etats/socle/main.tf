# TACHE 3, objectif 3 : le socle. FOURNI en partie.
#
# A COMPLETER : les deux sorties que l'application consommera. Un contrat entre
# deux racines se declare en sorties ; ce qui n'est pas expose n'existe pas pour
# l'autre.

resource "random_pet" "reseau" {
  length = 2

  keepers = {
    zone = var.zone
  }
}

variable "zone" {
  type    = string
  default = "eu-west-3a"
}

output "identifiant_reseau" {
  description = "Ce que l'application doit consommer."
  value       = ???
}

output "zone" {
  description = "La zone, pour que l'application n'ait pas a la redeclarer."
  value       = ???
}
