# Fourni. Une variable par marche de la cascade de precedence, plus celle qui
# nomme la ressource a renommer.

variable "par_defaut" {
  description = "Ne recoit jamais de valeur : son default gagne par forfait."
  type        = string
  default     = "gagnant-default"
}

variable "par_environnement" {
  description = "Fournie par TF_VAR_, et par rien d'autre."
  type        = string
  default     = "perdant-default"
}

variable "par_fichier" {
  description = "Posee dans terraform.tfvars ET dans TF_VAR_ : une seule gagne."
  type        = string
  default     = "perdant-default"
}

variable "par_ligne_de_commande" {
  description = "Posee partout. Une seule source gagne contre toutes les autres."
  type        = string
  default     = "perdant-default"
}
