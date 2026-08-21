# LES SORTIES DU MODULE, A ECRIRE.
#
# Une sortie n'est pas qu'une valeur : elle porte un type, une description, et
# peut refuser de se publier.

# ??? : un objet reprenant `nom`, `retention_jours`, `chiffre` et `etiquette`.
# C'est le resume que l'appelant lira, et il doit montrer les defauts combles.
output "resume" {
  ???
}

# ??? : le secret produit par `random_password.this`. Il traverse la frontiere
# du module : reflechissez a ce qui doit l'accompagner pour que la racine puisse
# le republier sans que le plan echoue.
output "secret" {
  ???
}

# ??? : le chemin du fichier, `local_file.this.filename`. Cette sortie ne doit
# PAS se publier quand le depot n'est pas chiffre : le plan doit s'arreter, avec
# un message explicite.
output "chemin" {
  ???
}
