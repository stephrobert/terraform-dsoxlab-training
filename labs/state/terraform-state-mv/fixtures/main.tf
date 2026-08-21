# Code DEJA REFACTORE par l'equipe precedente, a ne pas modifier.
#
# Les trois objets existent bel et bien : ils sont dans terraform.tfstate, mais
# aux ANCIENNES adresses. Personne n'a reconcilie le state apres le refactoring,
# et c'est tout le sujet du lab. Le premier `terraform plan` annonce donc trois
# creations et trois destructions : Terraform ne voit pas un renommage, il voit
# des ressources disparues et d'autres apparues.

terraform {
  required_version = ">= 1.1"
  required_providers {
    random = { source = "hashicorp/random", version = "~> 3.6" }
  }
}

# Anciennement random_pet.web
resource "random_pet" "frontend" {
  length = 2
}

# Anciennement random_integer.web_port
resource "random_integer" "frontend_port" {
  min = 8000
  max = 8999
}

# Anciennement random_string.db_secret, a la racine : la ressource est passee
# DANS un module, ce qui change aussi son adresse.
module "secret" {
  source = "./modules/secret"
}
