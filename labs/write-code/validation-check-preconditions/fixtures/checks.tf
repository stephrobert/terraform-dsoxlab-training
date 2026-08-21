# Niveau 4 : le bloc `check`. Il SURVEILLE sans bloquer : un assert en echec
# laisse l'apply reussir (contrairement aux trois autres niveaux). Son data
# source SCOPE est relu a CHAQUE plan, ce qui a une consequence a connaitre
# (voir le guide : plan -detailed-exitcode).
check "lot_au_maximum" {
  data "local_file" "relu" {
    filename = local_file.manifeste.filename
  }

  # ??? assert : le manifeste devrait compter taille_max lignes. Avec
  #     taille_lot (2) < taille_max (5), cet assert ECHOUE a dessein : c'est ce
  #     qui montre qu'un check en echec avertit sans bloquer l'apply.
  assert {
    condition     = ???
    error_message = ???
  }
}
