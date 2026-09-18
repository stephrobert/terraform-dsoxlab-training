# Trois sorties, toutes trouees.
#
# La troisieme est particuliere : elle doit etre declaree sensible. Observez
# ensuite ou la valeur est masquee, et ou elle ne l'est pas.

output "nom_animal" {
  value = ???
}

output "chemin_rapport" {
  value = ???
}

output "nom_majuscule" {
  value     = ???
  sensitive = ???
}
