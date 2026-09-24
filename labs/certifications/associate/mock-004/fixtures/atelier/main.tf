# L'atelier. A COMPLETER : chaque ??? porte au-dessus de lui ce qu'on attend.
#
# Quatre ressources gerees, un seul bloc `data`. Les quatre dernieres questions
# de l'examen portent sur l'etat que ce repertoire produit : elles n'ont de
# reponse qu'une fois ce fichier complete et applique.

resource "random_pet" "socle" {
  length    = 2
  separator = "-"
}

resource "local_file" "modele_source" {
  filename = "${path.module}/modele.txt"
  content  = "socle=${random_pet.socle.id}\n"

  # A COMPLETER, le bloc lifecycle, avec TROIS choses :
  #
  #   - la regle qui fait CREER le nouveau fichier avant de detruire l'ancien,
  #     de sorte qu'un remplacement ne laisse aucune fenetre a vide ;
  #   - une `precondition` qui refuse AU PLAN une empreinte plus courte que
  #     `var.longueur_minimale` ;
  #   - une `postcondition` qui relit le fichier ecrit, par `self`, et exige
  #     qu'il ne soit pas vide.
  #
  # Chaque condition porte son `error_message`, qui est obligatoire.
  ???
}

# A COMPLETER : cette data source doit lire le fichier PRODUIT par la ressource
# ci-dessus. Referencez son attribut plutot que de recomposer le chemin : c'est
# la reference qui cree la dependance.
data "local_file" "modele" {
  filename = ???
}

resource "terraform_data" "jeton" {
  input = var.empreinte
}

resource "null_resource" "garde" {
  triggers = {
    socle = random_pet.socle.id
  }

  # A COMPLETER : cette ressource doit attendre que la data source ait ete lue,
  # alors qu'elle n'utilise AUCUNE de ses donnees. Aucune reference ne peut
  # exprimer ce lien.
  ???
}

# A COMPLETER : un bloc `check` au niveau racine, nomme `modele_lisible`, qui
# AVERTIT sans bloquer si le contenu lu par la data source est vide.
#
# Attention : un `check` qui interrogerait une donnee relue a chaque plan
# ramenerait un code 2, et la question q39 attend 0.
???
