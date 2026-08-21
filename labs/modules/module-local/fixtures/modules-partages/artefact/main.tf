# Module partage : produit un artefact nomme.
# CE MODULE EST COMPLET, ne pas le modifier.
#
# Notez son propre appel de module, en `../nom` : un module local peut en
# appeler un autre, et le chemin est relatif AU MODULE, pas au projet racine.

terraform {
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

variable "nom" {
  description = "Nom de base de l'artefact."
  type        = string
}

variable "suffixe_aleatoire" {
  description = "Ajoute un suffixe aleatoire au nom de l'artefact."
  type        = bool
  default     = true
}

module "nom" {
  source = "../nom"

  base              = var.nom
  suffixe_aleatoire = var.suffixe_aleatoire
}

resource "local_file" "this" {
  filename = "${path.root}/artefacts/${module.nom.complet}.txt"
  content  = "artefact ${module.nom.complet}\n"
}

output "chemin" {
  description = "Chemin du fichier produit."
  value       = local_file.this.filename
}

output "configuration" {
  description = "Ce que l'appelant a reellement demande."
  value = {
    nom               = var.nom
    suffixe_aleatoire = var.suffixe_aleatoire
  }
}
