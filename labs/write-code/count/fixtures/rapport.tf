# Le rapport est optionnel : zero instance quand `rapport` est faux, une seule
# quand il est vrai. Choisissez le meta-argument qui produit 0 ou 1 instance
# selon le booleen.
resource "local_file" "rapport" {
  ??? = var.rapport ? 1 : 0

  filename = "${path.module}/rapport.txt"
  content  = "genere\n"
}
