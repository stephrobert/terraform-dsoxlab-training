# Version count d'origine de `local_file.service`, figee. Le test de migration
# l'applique pour reconstituer l'etat AVANT (service[0], [1], [2]), puis superpose
# la configuration migree de l'apprenant pour prouver que les blocs `moved`
# rendent la migration non destructrice. Ne pas modifier.
resource "local_file" "service" {
  count    = length(var.services)
  filename = "${path.module}/out/service-${var.services[count.index]}.txt"
  content  = "service=${var.services[count.index]}\n"
}
