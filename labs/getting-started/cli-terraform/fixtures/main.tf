# Configuration de depart du lab `cli-terraform`.
#
# Elle porte TROIS defauts, poses volontairement :
#   1. ce fichier n'est pas au format canonique ;
#   2. il reference une variable qui n'est declaree nulle part ;
#   3. aucun output n'expose les valeurs calculees.
#
# A vous de les corriger, sans changer ce que la configuration produit.

resource "random_pet" "nom" {
    length = 2
    separator = "-"
}

resource "local_file" "rapport" {
    filename = "${path.module}/rapport.txt"
    content = "Service ${var.nom_service} pour ${random_pet.nom.id}.\n"
}

resource "null_resource" "marqueur" {
    triggers = {
        nom = random_pet.nom.id
    }
}
