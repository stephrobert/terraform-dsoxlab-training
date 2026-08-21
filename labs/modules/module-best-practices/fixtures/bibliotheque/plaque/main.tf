terraform {
  required_providers {
    local = { source = "hashicorp/local", version = ">= 2.5" }
  }
}

# Ce module est un module « legacy » : il configure lui-meme son provider, et il
# fabrique la dependance dont il a besoin au lieu de la recevoir. Les deux sont a
# corriger, sans changer ce qu'il produit.
provider "local" {}

variable "nom" {
  type        = string
  description = "Nom porte par la plaque."
}

locals {
  # Le module decide seul de l'endroit ou il ecrit. L'appelant n'a pas voix au
  # chapitre, et ne peut donc pas brancher le module ailleurs.
  repertoire = "plaques"
}

resource "local_file" "plaque" {
  filename = "${path.root}/${local.repertoire}/${var.nom}.txt"
  content  = "plaque ${var.nom}\n"
}

output "chemin" {
  value       = local_file.plaque.filename
  description = "Chemin de la plaque produite."
}
