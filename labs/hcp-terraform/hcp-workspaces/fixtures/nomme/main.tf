# TROIS FAUTES, et elles ne tombent pas au meme endroit.
#
# Lancez `terraform validate` PUIS `terraform init`, et comparez. Mesure du
# 2026-09-25 : validate repond « Success! The configuration is valid. » sur deux
# de ces trois fautes. Seul l'init les voit.
#
# Ce repertoire doit se rattacher PAR NOM au workspace `app-prod` de
# l'organisation `atelier-dsoxlab`.

variable "organisation" {
  description = "Le nom de l'organisation."
  type        = string
  default     = "atelier-dsoxlab"
}

terraform {
  required_version = ">= 1.11.0"

  # FAUTE 1 : ce bloc ne peut pas cohabiter avec un bloc `cloud`. C'est la
  # seule des trois que `validate` attrape.
  backend "local" {}

  cloud {
    # FAUTE 2 : un bloc `cloud` est resolu AVANT toute evaluation d'expression.
    # Il ne peut donc referencer aucune valeur nommee.
    organization = var.organisation

    workspaces {
      # FAUTE 3 : ces deux arguments s'excluent. Un repertoire se rattache par
      # un nom OU par des etiquettes, jamais les deux.
      name = "app-prod"
      tags = ["prod", "app"]
    }
  }
}
