# Ce fichier est DISCUTABLE, et c'est voulu. Reprenez-le.
#
# La contrainte ci-dessous vient d'un guide repandu. Elle ne fait PAS ce que la
# plupart des gens croient.
#
#   ~> 0.8   autorise 0.8.0, 0.8.9, 0.9.0, 0.9.9...
#
# L'operateur pessimiste incremente le composant le plus a DROITE de ce qui est
# ecrit. Avec deux composants, c'est le mineur qui flotte : `~> 0.8` accepte
# donc toute la serie 0.x a partir de 0.8.
#
# Or la branche 0.9 a REECRIT le schema de presque toutes les ressources. Un
# code ecrit pour 0.9 casse net si un verrou le ramene en 0.8, et l'inverse est
# tout aussi vrai. Le message d'erreur parlera d'un argument inattendu, jamais
# d'une version.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    libvirt = {
      source  = "dmacvicar/libvirt"
      version = "~> 0.8"
    }
  }
}
