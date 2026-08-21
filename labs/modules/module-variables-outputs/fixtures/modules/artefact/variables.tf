# LES ENTREES DU MODULE, A ECRIRE.
#
# C'est ici que se joue le contrat : ce que l'appelant DOIT fournir, ce qu'il
# PEUT omettre, et ce que le module refuse.
#
# Rappel utile : `default` rend une variable facultative, mais ne protege pas
# d'un `null` passe explicitement, et ne dit rien des attributs d'un objet.

# ??? : un objet a trois attributs.
#   nom             string, REQUIS
#   retention_jours number, facultatif, 7 par defaut
#   chiffre         bool,   facultatif, true par defaut
# L'appel minimal de main.tf ne fournit que `nom` : le module doit combler le
# reste tout seul, sans que le plan echoue sur un objet incomplet.
variable "depot" {
  ???
}

# ??? : une chaine, "artefact" par defaut, et un `null` explicite doit donner
# CE defaut, pas une valeur nulle.
variable "etiquette" {
  ???
}

# ??? : un nombre, 16 par defaut, REFUSE hors de l'intervalle 12 a 64, avec un
# message qui nomme les bornes.
variable "longueur_secret" {
  ???
}
