# PROJET FIGE, a completer.
#
# Celui-ci sert de CONTRE-EXEMPLE : il doit montrer ce que Terraform fait d'un
# chemin qui n'est PAS local a ses yeux. Il ne sera jamais applique, seulement
# initialise.
#
# ??? : le `source`, en chemin ABSOLU vers modules-partages/nom. Un chemin
# absolu est pourtant bien sur le disque, mais Terraform le traite comme un
# paquet distant : regardez ce que l'init affiche, puis ce que
# .terraform/modules/modules.json enregistre.
#
# `path.cwd` peut vous aider a le construire sans coder votre arborescence en
# dur, mais un chemin ecrit a la main convient tout autant.

terraform {
  required_providers {
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

module "nom" {
  source = "???"

  base = "fige"
}
