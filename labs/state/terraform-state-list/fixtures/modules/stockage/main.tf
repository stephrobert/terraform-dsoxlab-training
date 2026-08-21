# Module local. Sa raison d'etre : produire des adresses prefixees
# module.stockage., et surtout une data source DANS un module, dont l'adresse
# ne commence donc PAS par « data ».

variable "retentions" {
  description = "Les politiques de retention, une archive par entree."
  type        = list(string)
}

resource "random_pet" "archive" {
  for_each = toset(var.retentions)
  length   = 2
}

resource "local_file" "index" {
  filename = "${path.root}/index-archives.txt"
  content  = "archives=${length(random_pet.archive)}\n"
}

# module.stockage.data.local_file.relecture : c'est CETTE entree que la recette
# `state list | grep -v ^data | wc -l` compte a tort comme une ressource geree.
data "local_file" "relecture" {
  filename   = local_file.index.filename
  depends_on = [local_file.index]
}

output "ids" {
  description = "Identifiant de chaque archive, par politique de retention."
  value       = { for cle, pet in random_pet.archive : cle => pet.id }
}
