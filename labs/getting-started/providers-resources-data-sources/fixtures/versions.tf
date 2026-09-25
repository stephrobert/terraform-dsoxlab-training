# A COMPLETER.
#
# Trois providers sont utilises par ce lab : `local`, `null` et `random`.
# Declarez-les avec leur source et une contrainte de version PESSIMISTE (`~>`),
# celle qui laisse flotter le dernier composant ecrit.
#
# Rappel de l'operateur, qui surprend avec deux composants :
#
#   ~> 2.5    accepte 2.9, refuse 3.0    le MINEUR flotte
#   ~> 2.5.0  accepte 2.5.9, refuse 2.6  le CORRECTIF flotte
#
# `terraform init` echoue tant que ce bloc est incomplet.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    ???
  }
}
