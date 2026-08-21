variable "seuil" {
  type        = number
  description = "Un nombre, pour illustrer conversion et precedence."
  default     = 3
}

variable "perm_forcee" {
  type        = string
  description = "Permission a forcer sur le fichier ; vide = laisser le defaut."
  default     = ""
}
