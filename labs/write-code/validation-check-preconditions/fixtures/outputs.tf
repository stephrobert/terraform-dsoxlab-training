output "noms" {
  value = random_pet.lot[*].id

  # ??? une precondition sur un OUTPUT : le nombre de noms doit egaler
  #     taille_lot. Bloque le plan si l'invariant est faux.
  precondition {
    condition     = ???
    error_message = ???
  }
}
