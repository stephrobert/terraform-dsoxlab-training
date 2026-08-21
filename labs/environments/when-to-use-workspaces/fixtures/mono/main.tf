# ─────────────────────────────────────────────────────────────────────────────
# CONFIGURATION A ARBITRER. Repertoire en LECTURE : ne l'appliquez pas.
#
# Contexte, donne par l'equipe qui l'a ecrite :
#
#   « On sert dev et prod depuis ce repertoire, avec des workspaces. La prod est
#     geree par une autre equipe, qui a ses propres droits sur le stockage
#     d'etat : nous n'y avons pas acces, et eux n'ont pas les notres. »
#
# Votre travail commence par une decision : qu'est-ce qui, ici, releve encore
# des workspaces, et qu'est-ce qui n'en releve plus ?
# ─────────────────────────────────────────────────────────────────────────────

terraform {
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

locals {
  cidrs = {
    default = "10.0.0.0/24"
    dev     = "10.1.0.0/24"
    prod    = "10.2.0.0/24"
  }
}

# --- Le socle reseau : partage, et de cycle de vie long ---------------------

resource "random_pet" "reseau" {
  length = 2
}

resource "local_file" "reseau" {
  filename = "${path.root}/produits/reseau-${terraform.workspace}.conf"
  content  = "reseau ${random_pet.reseau.id} cidr ${local.cidrs[terraform.workspace]}\n"
}

# --- L'application : deployee souvent, et par une autre equipe en prod ------

resource "local_file" "app" {
  count = terraform.workspace == "prod" ? 3 : 1

  filename = "${path.root}/produits/app-${terraform.workspace}-${count.index}.conf"
  content  = "app ${count.index} sur reseau ${random_pet.reseau.id}\n"
}

output "cidr" {
  value = local.cidrs[terraform.workspace]
}
