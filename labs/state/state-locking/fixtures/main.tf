# Projet a completer. Deux trous, marques ???.
#
# Aucun provider externe : terraform_data est integre a Terraform, le lab se
# joue donc hors ligne.

terraform {
  required_version = ">= 1.15.0"

  # ??? : le chemin du state, HORS de la racine du projet.
  # Le laisser a la racine ne montre rien : c'est en le deplacant qu'on voit
  # ou le fichier de verrou atterrit reellement.
  backend "local" {
    path = ???
  }
}

# Ressource volontairement lente. Sans elle l'apply se termine avant qu'on ait
# le temps d'observer quoi que ce soit : il faut au moins quinze secondes de
# verrou tenu pour mener les mesures.
# ??? : la commande du provisioner.
resource "terraform_data" "lent" {
  input = "verrouillage"

  provisioner "local-exec" {
    command = ???
  }
}
