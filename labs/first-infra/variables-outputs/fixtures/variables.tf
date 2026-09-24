# Quatre variables, toutes trouees.
#
# `terraform plan` echoue en l'etat : `???` n'est pas du HCL valide.

variable "env" {
  description = "Environnement cible."
  type        = ???
  default     = "dev"

  # A completer : n'accepter que `dev`, `staging` et `prod`.
  #
  # `error_message` est OBLIGATOIRE dans un bloc `validation`, et il doit se
  # terminer par un point. C'est le seul texte que l'apprenant lira quand sa
  # valeur sera refusee : ecrivez-le pour lui.
  validation {
    condition     = ???
    error_message = ???
  }
}

# A completer : un nombre, par defaut 2, refuse hors de la plage 1 a 9.
variable "replicas" {
  ???
}

# A completer : un objet portant `cpu` (number) et `memory_mb` (number), avec
# un `default`.
#
# Un type complexe ne sert a rien s'il n'est pas CONSOMME : `sizing_total_mb`
# devra multiplier sa memoire par le nombre de replicas.
variable "sizing" {
  ???
}

# A completer : une chaine SANS default.
#
# Elle ne peut donc venir que de l'exterieur : `TF_VAR_region` ou `-var`.
variable "region" {
  ???
}
