# A COMPLETER.
#
# `catalogue.txt` est DEJA sur le disque. Terraform ne l'a pas cree, et ne doit
# pas le creer : il doit le LIRE.
#
# Chaque bloc ci-dessous porte un `???` sur ce qui decide de tout : sa nature.
# Un bloc qui cree et gere un objet, ou un bloc qui se contente de lire.

# A COMPLETER : ce bloc doit LIRE `catalogue.txt`. Choisissez sa nature.
??? "local_file" "catalogue" {
  filename = "${path.module}/catalogue.txt"
}

# A COMPLETER : celui-ci doit ECRIRE un fichier, dont le contenu derive de ce
# que le bloc precedent a lu. Referencez-le : ne recopiez pas la valeur.
#
# Une reference vers un bloc de lecture ne s'ecrit pas comme une reference vers
# un bloc gere. Le prefixe change.
??? "local_file" "resume" {
  filename = "${path.module}/resume.txt"
  content  = ???
}

# A COMPLETER : une valeur tiree au sort, donc connue seulement APRES creation.
??? "random_pet" "empreinte" {
  length = 2
}

# A COMPLETER : ce bloc depend des deux precedents, par ses `triggers`. Ils
# doivent porter A LA FOIS la valeur tiree au sort et ce que le catalogue
# contient.
??? "null_resource" "sceau" {
  triggers = {
    empreinte = ???
    catalogue = ???
  }
}
