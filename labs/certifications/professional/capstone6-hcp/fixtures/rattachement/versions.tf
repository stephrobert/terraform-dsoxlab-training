# A COMPLETER : le rattachement.
#
# Ce repertoire doit se rattacher au workspace `audit-conformite` de
# l'organisation `atelier-dsoxlab`, par son NOM.
#
# Deux rappels que la section vous a donnes, et qui servent ici :
#
#   - un bloc `cloud` est resolu AVANT toute evaluation d'expression. Il
#     n'accepte donc aucune valeur nommee, et repond « Variables not allowed » ;
#   - `name` et `tags` s'excluent : ce sont deux strategies de rattachement.
#
# Vous n'avez pas de compte, et ce n'est pas necessaire : une configuration
# correcte va jusqu'a la demande d'authentification et s'y arrete. C'est la
# frontiere, et c'est ce que les tests verifient.

terraform {
  required_version = ">= 1.11.0"

  ???
}
