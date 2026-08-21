# Fourni, a NE PAS modifier. Genere un mot de passe et ecrit un petit rapport
# NON secret (juste la longueur demandee). Tout le travail est dans outputs.tf.
resource "random_password" "admin" {
  length = var.longueur_mot_de_passe
}

resource "local_file" "rapport" {
  filename = "${path.module}/out/rapport.json"
  content = jsonencode({
    longueur = var.longueur_mot_de_passe
  })
}
