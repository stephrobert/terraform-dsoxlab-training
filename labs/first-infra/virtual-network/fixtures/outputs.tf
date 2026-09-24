# A completer : deux sorties.
#
# Le nom du reseau et sa passerelle, en REFERENCANT les attributs de la
# ressource. Les variables portent les memes valeurs, et les reprendre
# donnerait le meme texte : mais un output qui lit une variable n'apprend rien
# a Terraform, et ne prouve rien a personne.

output "nom_du_reseau" {
  value = ???
}

output "passerelle" {
  value = ???
}
