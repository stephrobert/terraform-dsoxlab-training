# TACHE 4, objectif 4 : factoriser en module SANS rien recreer.
#
# Trois environnements, trois fois le meme couple de ressources. Un module doit
# les remplacer, et l'examen insiste sur un point : les ressources deja creees
# ne doivent etre ni detruites ni recreees.
#
# A COMPLETER :
#
#   1. ecrire un module local sous `modules/environnement/`, qui prend un nom et
#      une taille, et produit le fichier et son empreinte ;
#   2. remplacer les trois blocs ci-dessous par trois appels au module ;
#   3. poser les blocs `moved` qui disent a Terraform ou chaque ressource a
#      demenage. Sans eux, le plan annonce trois destructions et trois
#      creations, ce qu'un `plan` de controle refusera.
#
# La preuve : apres refactorisation, `terraform plan -detailed-exitcode` rend 0,
# et les identifiants du state sont INCHANGES.

resource "local_file" "dev" {
  filename = "${path.module}/dev.txt"
  content  = "environnement dev, taille 1"
}

resource "local_file" "staging" {
  filename = "${path.module}/staging.txt"
  content  = "environnement staging, taille 2"
}

resource "local_file" "prod" {
  filename = "${path.module}/prod.txt"
  content  = "environnement prod, taille 4"
}

output "empreintes" {
  description = "L'empreinte de chaque environnement, par nom."
  value       = ???
}
