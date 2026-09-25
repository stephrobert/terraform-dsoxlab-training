# A COMPLETER : cinq `???`, qui lisent le flux du run et rien d'autre.
#
# Le flux enregistre dans `flux/run.jsonl` est le MEME que celui qu'une CLI
# recoit d'un run distant : « Running plan in HCP Terraform. Output will stream
# here. » Un message par ligne, chacun un objet JSON autonome, ce qui permet de
# l'afficher au fil de l'eau sans attendre la fin.
#
# Les types de messages que porte le flux d'un run qui a ECHOUE en cours de
# route :
#
#   version           une fois, au debut, avec la version de Terraform
#   planned_change    un par ressource que le plan compte changer
#   change_summary    le resume ANNONCE par le plan
#   apply_start       un par ressource dont l'application commence
#   apply_complete    un par ressource dont l'application a ABOUTI
#   apply_errored     un par ressource dont l'application a echoue
#   diagnostic        le detail de l'erreur, avec l'adresse fautive
#
# Le piege est dans cette liste, et il ne se voit qu'en la lisant deux fois.

locals {
  # A COMPLETER : la liste des messages, decodes.
  #
  # Un fichier JSONL n'est pas du JSON : c'est un objet par ligne. Il se
  # decoupe, puis chaque ligne se decode. La derniere ligne est vide, et un
  # `jsondecode("")` echoue : la garde vient donc AVANT le decodage.
  messages = ???
}

output "par_type" {
  description = "Combien de messages de chaque type le flux porte."

  # A COMPLETER : une map du type vers son nombre d'occurrences. Les types ne
  # s'ecrivent pas a la main : ils se lisent dans le flux.
  value = ???
}

output "resume_annonce" {
  description = "L'objet `changes` du resume que porte le flux."

  # A COMPLETER.
  #
  # Attention : sur un run qui aboutit, le flux porte DEUX `change_summary`,
  # l'un d'operation `plan` et l'autre d'operation `apply`. Sur un run qui
  # echoue, il n'en porte plus qu'UN. Regardez lequel avant d'ecrire le filtre.
  value = ???
}

output "adresses_abouties" {
  description = "Les adresses des ressources dont l'application a abouti, triees."

  # A COMPLETER : une liste triee. Le message qui prouve qu'une ressource a
  # abouti n'est pas celui qui annonce qu'elle va changer.
  value = ???
}

output "adresses_en_echec" {
  description = "Les adresses des ressources dont l'application a echoue, triees."

  # A COMPLETER : une liste triee.
  value = ???
}

output "ecart_entre_annonce_et_abouti" {
  description = "Combien de ressources annoncees n'ont pas abouti."

  # A COMPLETER : un nombre, calcule a partir des deux sorties precedentes.
  #
  # C'est tout l'interet de l'exercice. Le resume du flux dit ce que le plan
  # comptait faire ; il ne dit pas ce qui a ete fait. Sur un run interrompu,
  # s'y fier revient a croire une infrastructure dans un etat qu'elle n'a
  # jamais atteint.
  value = ???
}
