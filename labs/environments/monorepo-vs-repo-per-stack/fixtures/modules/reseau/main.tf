# Module local du monorepo. COMPLET : ne pas le modifier.
#
# Le CIDR est tire au sort a l'apply : aucune stack aval ne peut le deviner,
# elle doit le LIRE.

terraform {
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

resource "random_pet" "nom" {
  length = 2
}

resource "random_integer" "octet" {
  min = 20
  max = 250
}

resource "local_file" "reseau" {
  filename = "${path.root}/produits/reseau.conf"
  content  = "reseau ${random_pet.nom.id} cidr 10.${random_integer.octet.result}.0.0/16\n"
}

output "network_name" {
  description = "Nom du reseau produit."
  value       = random_pet.nom.id
}

output "network_cidr" {
  description = "Plage reseau tiree au sort a l'apply."
  value       = "10.${random_integer.octet.result}.0.0/16"
}
