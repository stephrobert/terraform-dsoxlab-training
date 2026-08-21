# Projet COMPLET, applicable en l'etat. Ne rien modifier ici : le seul fichier
# a completer est outputs.tf.
#
# Six ressources gerees et une data source, choisies pour couvrir les trois
# angles morts de `terraform state show` : un attribut SENSIBLE (caviarde), des
# attributs NULS (omis), et une ressource indexee par count (dont l'adresse sans
# index ne designe aucune instance).

resource "random_password" "api" {
  length = 24
}

resource "random_pet" "env" {
  length = 2
}

resource "random_pet" "replicas" {
  count  = 3
  length = 2
}

resource "local_file" "inventaire" {
  filename = "${path.root}/inventaire.txt"
  content  = "env=${random_pet.env.id}\n"
}

data "local_file" "relecture" {
  filename   = local_file.inventaire.filename
  depends_on = [local_file.inventaire]
}
