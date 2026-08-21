# Ce projet doit accepter TOUTE la serie 0.24 et au-dela dans les 0.x, sans
# jamais passer en 1.x : une contrainte SOUPLE, pas une version exacte. Le
# module vise est le meme que dans projet-epingle.
module "etiquette" {
  source  = "???"
  version = "???"

  namespace = "atelier"
  name      = "sud"
}

# Ce second appel vise le MEME module, mais il doit rester dans la serie de
# CORRECTIFS de la 0.24.1 : il accepte les 0.24.x et refuse la 0.25.0, pourtant
# disponible et plus recente. Deux versions du meme module cohabiteront donc
# dans ce seul projet.
module "etiquette_patch" {
  source  = "???"
  version = "???"

  namespace = "atelier"
  name      = "sud-patch"
}
