# ??? : declarer une valeur EPHEMERE, generee pendant l'operation mais JAMAIS
# ecrite dans le state ni dans le plan. Quel mot-cle de bloc produit une valeur
# ephemere a partir du provider random ? Remplacez ce ??? par le bon mot-cle.
??? "random_password" "jeton" {
  length = var.longueur
}

# Pour contraste : un random_password ORDINAIRE, dont le resultat EST persiste
# en clair dans le state. Ne pas modifier.
resource "random_password" "persistant" {
  length = var.longueur
}

# Un fichier marqueur NON secret. Ne pas y faire fuiter le jeton ephemere :
# une valeur ephemere dans un attribut persiste leve « Invalid use of ephemeral
# value ». Ne pas modifier.
resource "local_file" "marqueur" {
  filename = "${path.module}/out/marqueur.txt"
  content  = "longueur=${var.longueur}\n"
}
