terraform {
  required_providers {
    local = { source = "hashicorp/local", version = ">= 2.5" }
  }
}

# A completer : lire l'etat de la stack amont. Son backend est `local`, et son
# etat vit dans le repertoire voisin.
data "terraform_remote_state" "plateforme" {
  backend = "???"

  config = {
    path = "???"
  }
}

resource "local_file" "app" {
  filename = "${path.root}/produits/app.conf"

  # A completer : la valeur doit VENIR de la stack amont. Elle est tiree au
  # sort a l'apply, donc la recopier ne marchera pas deux fois.
  content = "app sur le reseau ??? en ???\n"
}
