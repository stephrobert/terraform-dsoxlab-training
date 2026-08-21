terraform {
  required_providers {
    local = { source = "hashicorp/local", version = ">= 2.5" }
  }
}

variable "environnement" {
  type        = string
  description = "Nom de l'environnement servi."
}

variable "repliques" {
  type        = number
  description = "Nombre de plaques a produire."
}

resource "local_file" "plaque" {
  count = var.repliques

  filename = "${path.root}/plaques/${var.environnement}-${count.index}.txt"
  content  = "plaque ${var.environnement} numero ${count.index}\n"
}

output "plaques" {
  value       = [for f in local_file.plaque : f.filename]
  description = "Chemins des plaques produites."
}

output "environnement" {
  value       = var.environnement
  description = "Environnement servi par cet appel."
}
