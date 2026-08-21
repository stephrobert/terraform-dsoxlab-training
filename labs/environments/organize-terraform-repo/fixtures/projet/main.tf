# Tout est ici : le bloc terraform, le provider, les variables, les ressources,
# les data sources et les sorties. Quatre-vingts lignes aujourd'hui, deux cents
# demain, et plus personne ne trouve rien.
terraform {
  required_version = ">= 1.11.0"

  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

provider "local" {}

provider "random" {}

variable "prefixe" {
  type        = string
  description = "Prefixe des artefacts produits."
  default     = "atelier"
}

variable "ateliers" {
  type        = set(string)
  description = "Ateliers pour lesquels produire une plaque."
  default     = ["nord", "sud"]
}

variable "commentaire" {
  type        = string
  description = "Commentaire inscrit en tete de l'inventaire."
  default     = "inventaire des plaques"
}

resource "random_pet" "jeton" {
  for_each = var.ateliers

  length = 2
}

resource "local_file" "plaque" {
  for_each = var.ateliers

  filename = "${path.root}/plaques/${var.prefixe}-${each.key}.txt"
  content  = "plaque ${var.prefixe}-${each.key} ${random_pet.jeton[each.key].id}\n"
}

resource "local_file" "inventaire" {
  filename = "${path.root}/plaques/inventaire.txt"
  content  = "${var.commentaire}\n${join("\n", sort([for p in local_file.plaque : p.filename]))}\n"
}

output "plaques" {
  value       = { for cle, fichier in local_file.plaque : cle => fichier.filename }
  description = "Chemin de chaque plaque produite."
}

output "inventaire" {
  value       = local_file.inventaire.filename
  description = "Chemin de l'inventaire."
}

output "jetons" {
  value       = { for cle, pet in random_pet.jeton : cle => pet.id }
  description = "Jeton tire pour chaque atelier."
}
