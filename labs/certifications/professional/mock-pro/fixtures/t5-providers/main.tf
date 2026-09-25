# TACHE 5, objectif 5 : deux configurations d'un meme provider.
#
# Deux repertoires de sortie. `public/` garde les droits par defaut, `prive/`
# doit etre ferme aux autres. Et les deux fichiers ne doivent pas etre rendus
# par la meme configuration de provider : l'exploitation veut pouvoir basculer
# la partie privee ailleurs sans toucher au reste.
#
# A COMPLETER :
#
#   1. une seconde configuration du provider `local`, portant un ALIAS ;
#   2. `local_file.prive` rattache explicitement a cette configuration. Une
#      ressource sans `provider` prend celle par defaut, silencieusement ;
#   3. sur cette meme ressource, les droits : 0600 pour le fichier, 0700 pour
#      le repertoire que Terraform cree au passage ;
#   4. dans `versions.tf`, la contrainte du provider, qui doit accepter toute la
#      serie 2 a partir de la 2.5 et refuser la 3.0.
#
# Ce que l'examen verifie derriere : savoir qu'un alias ne se devine pas, qu'une
# ressource ne change pas de configuration toute seule, et que les droits se
# posent sur la ressource. Le provider `local` n'accepte lui-meme AUCUN
# argument, ce qui se lit dans son schema : chercher a le configurer est une
# impasse, et c'est un piege classique.

???

resource "local_file" "public" {
  filename = "${path.module}/public/note.txt"
  content  = "lisible par tous"
}

resource "local_file" "prive" {
  filename = "${path.module}/prive/note.txt"
  content  = "reserve"
  ???
}
