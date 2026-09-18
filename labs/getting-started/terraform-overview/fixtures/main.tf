# Trois declarations, trois trous. Remplacez chaque ??? .
#
# Le point du lab n'est pas d'ecrire du HCL : c'est de comprendre ce que
# Terraform garde en memoire, et ce qu'il ignore.

# Un nom genere par le provider. Deux mots separes par un tiret.
resource "random_pet" "nom" {
  length    = ???
  separator = "-"
}

# Le rapport ecrit sur le disque. Son contenu doit etre CONSTRUIT a partir de
# l'identifiant produit ci-dessus, jamais recopie a la main : c'est cette
# reference qui cree la dependance entre les deux ressources.
resource "local_file" "rapport" {
  content  = ???
  filename = ???
}

# Une donnee seulement LUE. Elle ne cree rien, ne detruit rien, et n'a pas le
# meme statut dans le state qu'une ressource geree.
data "local_file" "inventaire" {
  filename = ???
}
