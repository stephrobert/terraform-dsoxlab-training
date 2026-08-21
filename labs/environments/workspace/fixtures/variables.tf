# Cette variable existe, elle est typee, elle a une valeur par defaut, et elle
# ressemble beaucoup a ce que le lab demande.
#
# C'est un piege. Une valeur d'environnement portee par une VARIABLE ne suit pas
# le workspace : elle est la meme partout tant qu'on ne la surcharge pas a
# chaque commande. Le nom du workspace courant, lui, se lit dans l'expression
# `terraform.workspace`.

variable "nom_env" {
  description = "Nom d'environnement fourni a la main. Ne suit PAS le workspace."
  type        = string
  default     = "dev"
}
