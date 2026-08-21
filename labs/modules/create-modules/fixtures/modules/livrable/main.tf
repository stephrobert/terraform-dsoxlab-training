# Le module enfant : il produit un livrable par environnement.
#
# ATTENTION : ce fichier porte un defaut herite d'un vieux copier-coller. Il
# fonctionnait tant que le module etait appele UNE fois. Lancez `terraform init`
# a la racine et lisez ce que Terraform en dit.

# --- Le defaut. A supprimer, une fois que vous aurez compris pourquoi. -------
provider "tls" {
  proxy {
    url = "http://proxy.interne.lan:3128"
  }
}

# L'etiquette du livrable, tiree au hasard.
resource "random_pet" "etiquette" {
  length = 2
}

# Le manifeste, ecrit par la configuration PAR DEFAUT du provider local.
resource "local_file" "manifeste" {
  filename = "${path.root}/livraisons/${var.nom}-manifeste.txt"
  content  = "${var.nom} vers ${var.cible}, retention ${var.retention} jours, ${random_pet.etiquette.id}\n"
}

# L'archive, ecrite par la configuration ALIASEE. Cette reference est ce qui
# oblige le module a declarer l'alias qu'il attend.
resource "local_file" "archive" {
  provider = local.archive

  filename = "${path.root}/livraisons/${var.nom}-archive.txt"
  content  = "archive ${var.nom} : ${random_pet.etiquette.id}\n"
}

# Le scellement du livrable. Le provider tls est configure a la RACINE.
resource "tls_private_key" "scellement" {
  algorithm = "ED25519"
}
