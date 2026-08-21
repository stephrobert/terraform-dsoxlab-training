# PROJET DEV, a completer.
#
# Ce projet doit lire le module partage LA OU IL EST, sans que Terraform en
# fasse une copie dans son cache.
#
# ??? : le `source`. Terraform ne considere un chemin comme LOCAL que s'il
# commence par `./` ou `../` : tout le reste, chemin absolu compris, est traite
# comme un paquet distant a recopier.
#
# Un argument de trop traine aussi dans ce bloc : il n'a de sens que pour un
# module de REGISTRE, et l'`init` vous dira ce qu'il en pense.

terraform {
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

module "artefact" {
  source  = "???"
  version = "~> 1.0"

  nom = "dev"
}
