# LE SEUL FICHIER A COMPLETER, et il ne regle qu'UN des trois deplacements.
#
# Les deux renommages a la racine se traitent en imperatif, par
# `terraform state mv` : le code est deja ecrit, seul le state est en retard.
#
# Le passage DANS le module, lui, se traite en declaratif, par ce bloc `moved` :
# il part du code, il se relit en revue, il se rejoue par toute l'equipe, et il
# reste dans l'historique. C'est la difference de fond entre les deux methodes.
#
# ??? : deux REFERENCES d'adresses, sans guillemets. `from` est l'adresse
# actuelle dans le state, `to` l'adresse voulue par le code refactore.

moved {
  from = ???
  to   = ???
}
