# Les workers sont de vraies copies interchangeables : aucune identite propre,
# on en veut juste `var.workers`. Choisissez le meta-argument qui cree N
# instances identiques indexees par entier.
resource "random_pet" "worker" {
  ??? = var.workers

  length = 2
}
