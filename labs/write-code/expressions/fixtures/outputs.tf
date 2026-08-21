output "ref_hote" {
  # ??? : l'id de la ressource random_pet nommee "hote". Une ressource geree se
  # reference SANS prefixe (aucun mot-cle "resource" dans une expression).
  value = ???
}

output "egalite_stricte" {
  # ??? : var.seuil (un nombre) est-il egal a la CHAINE "3" ? L'operateur ==
  # ne convertit PAS les types : anticipez le resultat.
  value = ???
}

output "calcul" {
  # ??? : 1 plus le double de var.seuil, en une seule expression. Attention a la
  # precedence des operateurs (* avant +).
  value = ???
}

output "perm_effective" {
  # ??? : la permission reellement appliquee a local_file.marqueur (pour prouver
  # que "" a bien ete traduit en omission).
  value = ???
}
