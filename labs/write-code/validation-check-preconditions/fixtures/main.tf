resource "random_pet" "lot" {
  count = var.taille_lot

  lifecycle {
    # ??? niveau 2 (precondition) : refuser AVANT la creation si taille_max
    #     depasse le garde-fou de 10. Evaluee au plan, pour chaque instance.
    precondition {
      condition     = ???
      error_message = ???
    }

    # ??? niveau 3 (postcondition) : refuser APRES la creation un nom vide.
    #     La postcondition est la SEULE a disposer de `self` (l'objet cree).
    postcondition {
      condition     = ???
      error_message = ???
    }
  }
}

resource "local_file" "manifeste" {
  filename = "${path.module}/manifeste.txt"
  content  = join("\n", random_pet.lot[*].id)
}
