# TACHE 2, objectif 2 : reparer la configuration et la rendre dynamique.
#
# Cette configuration ne valide pas. Elle porte TROIS fautes, et elle duplique
# ce qu'une seule declaration devrait produire.
#
# A COMPLETER :
#
#   1. les trois fautes se corrigent ; `terraform validate` les nomme une a une ;
#   2. les trois fichiers deviennent UNE ressource portee par `for_each` sur
#      `var.services`, chacun ecrivant « <nom> ecoute sur <port> » ;
#   3. la variable porte une `validation` qui refuse AU PLAN un port hors de
#      1024-65535, avec un message qui dit quoi corriger.

variable "services" {
  description = "Les services a decrire, par nom et par port."

  type = map(number)

  default = {
    api   = 8080
    web   = 8443
    batch = 9000
  }

  ???
}

# Les trois copies a remplacer par une seule ressource.
resource "local_file" "api" {
  filename = "${path.module}/api.txt"
  content  = "api ecoute sur ${var.services["api"]}"
}

resource "local_file" "web" {
  filename = "${path.module}/web.txt"
  content  = "web ecoute sur ${var.services[web]}"
}

resource "local_file" "batch" {
  filename = "${path.module}/batch.txt"
  content  = "batch ecoute sur ${var.services["batch"]}
}

output "fichiers" {
  description = "Les chemins ecrits, tries."
  value       = ???
}
