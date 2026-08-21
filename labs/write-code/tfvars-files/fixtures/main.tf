# Fourni (ne pas modifier). Ecrit un manifeste et expose les valeurs resolues.
resource "local_file" "manifest" {
  filename = "${path.module}/out/manifest.json"
  content = jsonencode({
    region   = var.region
    bucket   = var.bucket
    replicas = var.replicas
  })
}

output "region" {
  value = var.region
}

output "bucket" {
  value = var.bucket
}

output "replicas" {
  value = var.replicas
}
