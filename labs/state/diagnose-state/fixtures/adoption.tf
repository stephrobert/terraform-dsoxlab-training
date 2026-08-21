# ADOPTION DU JETON HERITE, a completer.
#
# Le fichier `token-herite.txt` porte un jeton cree hors Terraform, connu d'un
# service tiers : il ne peut PAS etre regenere. Il faut l'adopter tel quel.
#
# Tout est livre EN COMMENTAIRE : la configuration s'applique donc telle quelle,
# ce qui vous permet de construire d'abord l'etat de reference. Decommentez ce
# bloc au moment de l'adoption, pas avant : applique trop tot, il ferait CREER
# un jeton aleatoire au lieu d'adopter celui qui existe.
#
# La politique de l'equipe impose 24 caracteres pour tout NOUVEAU jeton, et ce
# `length` ne changera pas. Le jeton herite, lui, en fait moins : la ressource
# devra donc etre adoptee SANS que Terraform ne cherche a l'aligner sur la
# configuration. Lisez le plan avant d'appliquer, il annonce ce qu'il va faire.
#
# ??? : le corps du bloc `lifecycle`, et les deux attributs du bloc `import`.

# resource "random_string" "legacy" {
#   length = 24
#
#   lifecycle {
#     ???
#   }
# }
#
# import {
#   to = ???
#   id = ???
# }
