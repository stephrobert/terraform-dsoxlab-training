# La stack AVAL. Elle ne cree pas de reseau, elle CONSOMME celui d'a cote.
#
# A COMPLETER : le bloc `terraform`, comme pour la stack amont.

terraform {
  ???
}

# A COMPLETER : la lecture de l'etat distant de `reseau/`.
#
# Les arguments sont les memes que ceux du backend de la stack amont, a une
# difference pres : ici on LIT, on ne verrouille pas. Et la cle designe l'etat
# de `reseau/`, pas le votre.
data "terraform_remote_state" "reseau" {
  backend = ???

  config = {
    ???
  }
}

resource "local_file" "raccordement" {
  filename = "${path.module}/raccordement.json"

  # A COMPLETER : un JSON serialise par une fonction, portant l'identifiant du
  # reseau, sa plage et sa passerelle.
  #
  # Ces trois valeurs viennent de l'etat distant. Les recopier ferait passer les
  # tests d'aujourd'hui et echouer celui qui change la plage en amont.
  content = ???
}

output "raccordement" {
  value = ???
}
