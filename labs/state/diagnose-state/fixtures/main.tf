# Configuration de reference, complete et applicable telle quelle.
#
# CE FICHIER N'EST PAS A MODIFIER : le travail porte sur le state et sur
# adoption.tf. Le premier `terraform init` puis `terraform apply` construit
# l'etat de reference dont part l'exercice.

terraform {
  required_version = ">= 1.7"
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

# Le fichier que quelqu'un ira bricoler a la main : c'est la derive a
# diagnostiquer, puis a reconcilier.
resource "local_file" "note" {
  filename = "${path.root}/data/note.txt"
  content  = "note de reference\n"
}
