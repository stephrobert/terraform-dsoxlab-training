# Fourni, complet. Aucun cloud, aucun hyperviseur : le parc est SIMULE par des
# ressources dont certains attributs ne sont connus qu'apres creation, comme
# une adresse allouee par un ordonnanceur.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
