# LE FICHIER A COMPLETER, pour la voie declarative.
#
# Le bloc est livre EN COMMENTAIRE : tant qu'il l'est, la configuration
# s'applique telle quelle, ce qui vous permet de mettre le projet en route par
# un premier `terraform init` puis `terraform apply`. Decommentez-le au moment
# ou vous en avez besoin.
#
# Un bloc `removed` sort une ressource du state. ATTENTION : son comportement
# par defaut est de DETRUIRE l'objet reel. Sans le bon argument dans le bloc
# `lifecycle`, vous ne cessez pas de gerer le fichier, vous le supprimez.
#
# ??? : l'adresse visee (une reference, sans guillemets ni cle d'instance), et
# la valeur de `destroy` qui conserve l'objet.

# removed {
#   from = ???
#
#   lifecycle {
#     destroy = ???
#   }
# }
