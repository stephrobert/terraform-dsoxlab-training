# Projet applique par l'equipe precedente : trois artefacts sur le disque.
#
# CE FICHIER N'EST PAS A MODIFIER. Il n'y a aucun `???` a completer : tout le
# travail porte sur le STATE, pas sur le HCL.

terraform {
  required_version = ">= 1.7"
  required_providers {
    local = { source = "hashicorp/local", version = ">= 2.5" }
  }
}

resource "local_file" "un" {
  filename = "${path.root}/artefacts/un.txt"
  content  = "artefact un\n"
}

resource "local_file" "deux" {
  filename = "${path.root}/artefacts/deux.txt"
  content  = "artefact deux\n"
}

resource "local_file" "trois" {
  filename = "${path.root}/artefacts/trois.txt"
  content  = "artefact trois\n"
}
