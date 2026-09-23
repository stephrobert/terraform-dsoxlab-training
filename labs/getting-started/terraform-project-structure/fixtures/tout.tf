# FOURNI. Un seul fichier, et tout dedans, dans le desordre.
#
# Terraform evalue TOUS les `.tf` d'un repertoire comme un document unique :
# le nom des fichiers et leur ordre n'ont aucun effet fonctionnel. Ce fichier
# marche donc parfaitement. Le probleme n'est pas qu'il soit casse, c'est qu'il
# soit illisible.
#
# Decouper ne doit RIEN changer au plan. C'est cela que le lab prouve.

output "environnement_effectif" {
  value = var.environnement
}

variable "projet" {
  type        = string
  description = "Nom du projet."
  default     = "atelier"
}

resource "random_pet" "nom" {
  length    = 2
  separator = "-"
}

provider "random" {
}

variable "environnement" {
  type        = string
  description = "Environnement cible."
  default     = "dev"
}

locals {
  etiquette = "${var.projet}-${var.environnement}"
}

terraform {
  required_version = ">= 1.5.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}

output "projet_effectif" {
  value = var.projet
}

provider "local" {
}

# Sans `default` et sans valeur en fichier : elle ne peut venir que de la
# ligne de commande.
variable "operateur" {
  type        = string
  description = "Qui applique la configuration."
}

resource "local_file" "rapport" {
  content  = "projet : ${var.projet}\nenvironnement : ${var.environnement}\noperateur : ${var.operateur}\netiquette : ${local.etiquette}\n"
  filename = "${path.module}/rapport.txt"
}

provider "null" {
}

output "operateur_effectif" {
  value = var.operateur
}

variable "region" {
  type        = string
  description = "Region, laissee a son defaut par le lab."
  default     = "eu-west-3"
}

resource "null_resource" "empreinte" {
  triggers = {
    etiquette = local.etiquette
  }
}
