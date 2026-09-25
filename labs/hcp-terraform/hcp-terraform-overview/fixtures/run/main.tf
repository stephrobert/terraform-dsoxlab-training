# Fourni. A NE PAS MODIFIER.
#
# Une seule ressource, dont le contenu vient d'une variable. C'est tout ce qu'il
# faut pour jouer un run en deux temps : le plan fige une valeur, l'apply pose
# cette valeur et rien d'autre.

variable "message" {
  description = "Ce que le rapport doit contenir."
  type        = string
}

resource "local_file" "rapport" {
  filename = "${path.module}/rapport.txt"
  content  = var.message
}
