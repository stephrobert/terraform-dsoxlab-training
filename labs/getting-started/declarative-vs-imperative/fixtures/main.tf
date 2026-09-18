# Le meme resultat que `imperatif.sh`, decrit autrement.
#
# Le script dit COMMENT faire, etape par etape. Ici vous dites QUOI obtenir, et
# c'est Terraform qui decide des etapes. Toute la difference est dans ce que
# produit un second passage.

# L'identifiant. Il ne se tire pas a chaque appel : il est memorise dans le
# state, et n'est regenere que si ce dont il depend change.
resource "random_string" "identifiant" {
  length  = ???
  special = ???
  upper   = ???

  # Ce qui decide de sa stabilite. Tant que ces valeurs ne bougent pas,
  # l'identifiant ne bouge pas.
  keepers = ???
}

# Le rapport. Contrairement au script, il est REMPLACE et non empile : son
# contenu decrit un etat, pas un historique.
resource "local_file" "rapport" {
  content  = ???
  filename = ???
}

# Une ressource dont le declencheur depend de l'identifiant : elle ne sera
# remplacee que si l'identifiant change.
resource "null_resource" "empreinte" {
  triggers = ???
}
