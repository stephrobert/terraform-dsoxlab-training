# PROJET STAGING, a completer entierement.
#
# Meme module partage que dev, mais un autre nom et, cette fois, SANS suffixe
# aleatoire : c'est a l'appelant de le dire, puisque le module active le
# suffixe par defaut.
#
# ??? : le `source`, et les deux arguments.

terraform {
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

module "artefact" {
  source = "???"

  ???
}
