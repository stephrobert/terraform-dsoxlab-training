# A COMPLETER : le rattachement.
#
# Ce repertoire doit s'executer DANS le workspace que `plateforme/` vient de
# creer. Tout ce qui manque est un bloc `cloud`, et vous savez deja tout ce
# qu'il faut pour l'ecrire : le lab `hcp-workspaces` l'a etabli.
#
# Deux rappels, mesures le 2026-09-25, qui vont vous servir ici :
#
#   - un bloc `cloud` est resolu AVANT toute evaluation d'expression. Il
#     n'accepte donc pas `var.organisation`, et repond « Variables not
#     allowed ». Le nom s'ecrit en toutes lettres ;
#   - `name` et `tags` s'excluent. Ici, vous visez UN workspace precis.
#
# Les valeurs a employer sont celles que `terraform output` vous a rendues dans
# `plateforme/`.

terraform {
  required_version = ">= 1.11.0"

  ???

  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
  }
}
