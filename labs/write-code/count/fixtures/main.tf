# VERSION PIEGEE, volontairement applicable telle quelle. `local_file.service`
# est indexe par POSITION (count.index) : retirer un service du milieu de la
# liste decale tous les suivants et fait recreer/detruire des objets voisins.
#
# Votre travail : APRES un premier `init` + `apply` (qui pose service[0..2]),
# migrer ce bloc vers `for_each` keye par nom, et ajouter les blocs `moved`
# qui relient chaque ancien index a sa nouvelle cle, pour que la migration
# ne detruise AUCUN objet.
resource "local_file" "service" {
  count    = length(var.services)
  filename = "${path.module}/out/service-${var.services[count.index]}.txt"
  content  = "service=${var.services[count.index]}\n"
}
