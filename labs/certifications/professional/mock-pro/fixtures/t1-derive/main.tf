# TACHE 1, objectif 1 : reconcilier une derive.
#
# `existant.txt` a ete modifie A LA MAIN, hors de Terraform. La configuration
# ci-dessous decrit autre chose, et un `plan` le voit.
#
# Deux facons de reconcilier, et l'examen attend la seconde :
#
#   - ecraser : appliquer la configuration telle quelle, et perdre ce que
#     quelqu'un a ecrit ;
#   - ADOPTER l'etat reel : faire decrire a la configuration ce qui existe
#     vraiment, puis verifier que le plan ne propose plus rien.
#
# A COMPLETER : le `content`, qui doit valoir EXACTEMENT ce que le fichier
# contient aujourd'hui. Lisez-le avant d'ecrire : c'est tout l'exercice.
#
# La preuve attendue : le fichier garde son contenu, et
# `terraform plan -detailed-exitcode` rend 0.

resource "local_file" "inventaire" {
  filename = "${path.module}/existant.txt"
  content  = ???
}
