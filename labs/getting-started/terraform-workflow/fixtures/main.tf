# FOURNI, complet, a ne pas modifier.
#
# Cinq ressources, une seule variable. Elles ne reagissent PAS toutes de la
# meme facon a un changement de cette variable, et c'est tout le sujet : la
# sortie humaine du plan annonce les deux cas dans le meme bloc de texte.
#
# `terraform_data` est une ressource integree, sans provider externe. Son
# argument `input` se met a jour EN PLACE ; son `triggers_replace`, lui, force
# un remplacement. Les deux sont ici, sur deux ressources differentes.

variable "etiquette" {
  type        = string
  description = "Marque portee par toutes les ressources du projet."
}

# `input` seul : une mise a jour en place.
resource "terraform_data" "configuration" {
  input = var.etiquette
}

# `triggers_replace` : un remplacement, meme si `input` pourrait se mettre a
# jour tout seul.
resource "terraform_data" "jeton" {
  triggers_replace = [var.etiquette]
  input            = var.etiquette
}

resource "local_file" "rapport" {
  content  = "etiquette : ${var.etiquette}\n"
  filename = "${path.module}/rapport.txt"
}

resource "random_string" "cle" {
  length  = 10
  special = false

  keepers = {
    etiquette = var.etiquette
  }
}

resource "null_resource" "empreinte" {
  triggers = {
    etiquette = var.etiquette
  }
}
