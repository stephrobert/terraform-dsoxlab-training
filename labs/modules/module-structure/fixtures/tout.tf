# TOUT EST ICI, ET C'EST BIEN LE PROBLEME.
#
# Ce fichier unique empile le bloc `terraform`, les variables, les ressources et
# la sortie, dans le desordre. Il fonctionne, mais aucun outil ne sait le lire :
# ni le registre, ni les generateurs de documentation, ni un relecteur presse.
#
# Deux `???` l'empechent meme d'etre analyse. Commencez par eux.

variable "nom_service" {
  type        = string
  description = "Nom du service documente par les fiches."
  default     = "annuaire"
}

resource "local_file" "index" {
  filename        = "${path.root}/index.txt"
  content         = "index des fiches du service ${var.nom_service}\n"
  file_permission = var.permissions_index
}

terraform {
  required_version = ">= 1.7"
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

# ??? : le type de cette variable. Elle porte les noms d'environnements, et le
# code plus bas l'utilise comme une collection iterable.
variable "environnements" {
  type        = ???
  description = "Environnements pour lesquels une fiche est produite."
  default     = ["dev", "prod"]
}

# Une seule etiquette pour tous les environnements : apres refactoring, chaque
# environnement aura la sienne, produite par le module imbrique.
resource "random_pet" "id" {
  length = 2
}

# Cette sortie est incomplete a deux titres. Le style guide 1.15 demande, sur
# CHAQUE output, un `type` et une `description`, dans l'ordre `Type, Description,
# Value, Sensitive` : « Like you would for variables, provide a type and
# description for each output ». Il manque ici la ligne `type`, et la description
# est a ecrire.
#
# La difference n'est pas cosmetique : sans `type` declare, `terraform output
# -json` rend le type INFERE, soit un `object` decrivant chaque cle, la ou un
# `map(string)` declare ressort en `["map","string"]`.
output "chemins" {
  # ??? : la description de cette sortie.
  description = ???
  value       = { for nom in var.environnements : nom => "${path.root}/fiches/${nom}.txt" }
}

variable "permissions_index" {
  type        = string
  description = "Permissions du fichier d'index, en notation octale."
  default     = "0644"
}
