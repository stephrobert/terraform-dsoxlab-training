# Deux natures de blocs cohabitent ici, et un seul mot les separe.
#
# `catalogue.txt` existe deja sur le disque. Personne ne l'a cree avec
# Terraform, et Terraform ne doit jamais le detruire. Le bloc ci-dessous doit
# le LIRE, pas le gerer.

??? "local_file" "catalogue" {
  filename = "${path.module}/catalogue.txt"
}

resource "random_pet" "reference" {
  length    = 2
  separator = "-"
}

# Ce fichier-la, en revanche, est cree et detruit par Terraform. Son contenu
# doit DERIVER de ce que le bloc precedent a lu : c'est cette reference qui
# cree la dependance, et elle s'ecrit autrement selon la nature du bloc vise.
resource "local_file" "resume" {
  content  = ???
  filename = "${path.module}/resume.txt"
}

# Le declencheur depend des DEUX : la valeur produite par la resource, et ce
# que la source de donnees a lu.
resource "null_resource" "empreinte" {
  triggers = {
    reference = ???
    catalogue = ???
  }
}
