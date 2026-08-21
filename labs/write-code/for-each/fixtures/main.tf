# Configuration CORRECTE mais FRAGILE : les instances sont adressees par
# position. Inserer un service au milieu de la liste decale tous les index
# suivants.

resource "random_pet" "service" {
  count  = length(var.services)
  length = 2
}

resource "local_file" "fiche" {
  count    = length(var.services)
  filename = "${path.module}/out/${var.services[count.index]}.txt"
  content  = "service=${var.services[count.index]}\nidentite=${random_pet.service[count.index].id}\n"
}
