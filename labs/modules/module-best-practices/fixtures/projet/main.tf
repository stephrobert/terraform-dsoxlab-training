terraform {
  required_providers {
    local = { source = "hashicorp/local", version = ">= 2.5" }
  }
}

# Ce projet doit produire DEUX plaques a partir du meme module, sans dupliquer
# l'appel, et decider lui-meme du repertoire de sortie.
module "plaque" {
  source = "../bibliotheque/plaque"

  nom = "nord"
}
