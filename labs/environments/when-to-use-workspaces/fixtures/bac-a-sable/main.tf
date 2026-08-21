# Le cas ou les workspaces restent LEGITIMES : une meme infrastructure, des
# variations legeres, les memes droits, le meme backend.
#
# Ici, pas de credentials distincts, pas de decoupe en sous-systemes : juste une
# taille qui change d'un environnement a l'autre.

terraform {
  required_providers {
    local = { source = "hashicorp/local", version = ">= 2.5" }
  }
}

locals {
  tailles = {
    default = 1
    dev     = 2
    prod    = 8
  }
}

resource "local_file" "app" {
  filename = "${path.root}/produits/app-${terraform.workspace}.conf"

  # A completer : la taille doit venir de la map ci-dessus, indexee par le
  # workspace COURANT, avec un repli sur l'entree `default` si le workspace n'y
  # figure pas.
  content = "taille ${???}\n"
}

output "taille" {
  description = "Taille retenue pour le workspace courant."
  value       = ???
}
