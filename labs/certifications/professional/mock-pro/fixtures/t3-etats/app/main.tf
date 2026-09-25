# TACHE 3, objectif 3 : l'application, qui lit l'etat du socle.
#
# A COMPLETER : trois choses.
#
#   1. la source de donnees qui lit l'etat du socle. Le backend est `local`, et
#      son chemin pointe le state du repertoire voisin ;
#   2. le contenu du fichier, qui doit citer l'identifiant venu du socle ;
#   3. la sortie qui republie cet identifiant.
#
# Rien ne doit etre recopie en dur : un test rejoue le socle avec une autre
# zone et verifie que l'application suit.

???

resource "local_file" "app" {
  filename = "${path.module}/app.txt"
  content  = ???
}

output "reseau_consomme" {
  description = "L'identifiant lu chez le socle."
  value       = ???
}
