# Fourni, a NE PAS modifier. Ce fichier consomme les variables et fixe donc les
# types attendus : `nodes` est parcourue comme une map d'objets, `retention_days`
# comme un nombre, `env` comme une chaine, `db_password` comme une chaine sensible.
resource "random_password" "db" {
  length = 16
}

resource "local_file" "manifest" {
  filename = "${path.module}/out/manifest.json"

  content = jsonencode({
    env            = var.env
    retention_days = var.retention_days
    nodes          = var.nodes
  })
}

output "env" {
  value = var.env
}

output "retention_days" {
  value = var.retention_days
}

output "nodes" {
  value = var.nodes
}

output "db_password" {
  value     = var.db_password
  sensitive = true
}

output "generated_secret" {
  value     = random_password.db.result
  sensitive = true
}
