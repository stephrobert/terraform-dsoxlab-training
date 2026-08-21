terraform {
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

module "reseau" {
  source = "../../modules/reseau"

  # Cette ligne est de trop, et elle empeche l'initialisation. Terraform dit
  # pourquoi : lisez ce qu'il repond.
  version = "???"
}

# Un secret de la plateforme. Il a sa place dans CET etat, jamais dans les
# sorties racine : tout ce qui sort ici devient lisible par les stacks aval.
resource "random_password" "db" {
  length  = 24
  special = true
}
