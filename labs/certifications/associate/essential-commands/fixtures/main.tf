# Ce fichier est MAL INDENTE et troue. Les deux se corrigent.

resource "random_pet" "ancien_nom" {
    length = 2
     separator = "-"
}

resource "local_file" "rapport" {
  filename = "${path.module}/rapport.txt"
    content = "identifiant : ${random_pet.???.id}\n"
}

# Le fichier `etat/preexistant.txt` existe deja sur le disque. Une ressource
# doit le prendre en charge, sans toucher a son contenu.
resource "local_file" "adopte" {
  filename = "${path.module}/etat/preexistant.txt"
  content  = "Ce fichier existe deja. Personne ne l a cree avec Terraform.\n"
}

# Un objet « deja provisionne ailleurs », que le lab fera adopter par un bloc
# `import`. Son identifiant est connu : c'est tout ce qu'un import demande.
resource "terraform_data" "provisionne_ailleurs" {
  input = "identifiant-connu"
}

resource "null_resource" "a_remplacer" {
  triggers = {
    rapport = local_file.rapport.filename
  }
}
