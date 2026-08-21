# Le module produit un secret et un fichier de depot.
# CE FICHIER EST COMPLET : c'est l'INTERFACE du module qui est a ecrire, pas
# son contenu.

resource "random_password" "this" {
  length = var.longueur_secret
}

resource "local_file" "this" {
  filename = "${path.root}/depots/${var.depot.nom}.txt"
  content  = "${var.depot.nom} / ${var.etiquette} / retention ${var.depot.retention_jours}j\n"
}
