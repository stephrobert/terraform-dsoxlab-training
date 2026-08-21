# Module d'accueil, a ne pas modifier. L'objet qui doit le rejoindre existe
# deja : il est enregistre a la racine du state sous random_string.db_secret.

resource "random_string" "this" {
  length  = 20
  special = false
}

output "valeur" {
  description = "La chaine generee, telle qu'elle existe deja."
  value       = random_string.this.result
  sensitive   = true
}
