terraform {
  required_version = ">= 1.11.0"

  required_providers {
    local = { source = "hashicorp/local", version = ">= 2.5" }
  }

  # Backend PARTIEL : aucun argument ici. Le chemin de l'etat est fourni a
  # l'initialisation, ce qui permet a ce fichier d'etre IDENTIQUE dans tous les
  # environnements. Un `path = "../etats/${var.env}.tfstate"` ne marcherait pas :
  # « Error: Variables not allowed ».
  backend "local" {}
}

# Cet environnement doit consommer le module partage, avec ses propres valeurs.
module "plaques" {
  source = "???"

  ??? = ???
}

output "plaques" {
  value = module.plaques.plaques
}

output "environnement" {
  value = module.plaques.environnement
}
