# Projet applique par l'equipe precedente. Quatre ressources au state, dont deux
# doivent CESSER d'etre gerees par Terraform sans que les fichiers disparaissent.
#
# Ce fichier est a MODIFIER : retirer un bloc `resource` fait partie de
# l'exercice. Les deux temoins, eux, restent geres du debut a la fin.

terraform {
  required_version = ">= 1.1"
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

# Cible de la voie IMPERATIVE : `terraform state rm`.
resource "local_file" "rapport" {
  filename = "${path.root}/rapport.txt"
  content  = "rapport-origine\n"
}

# Cible de la voie DECLARATIVE : le bloc `removed` de retrait.tf.
resource "local_file" "archive" {
  filename = "${path.root}/archive.txt"
  content  = "archive-origine\n"
}

# Temoins : ils doivent rester geres, avec les memes valeurs.
resource "local_file" "conserve" {
  filename = "${path.root}/conserve.txt"
  content  = "temoin\n"
}

resource "random_pet" "identifiant" {
  length = 2
}
