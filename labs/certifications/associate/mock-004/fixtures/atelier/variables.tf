# Fourni, complet.

variable "empreinte" {
  description = "Une valeur que le lab traite comme un secret."
  type        = string
  sensitive   = true
  default     = "empreinte-de-demonstration"
}

variable "longueur_minimale" {
  description = "Longueur en dessous de laquelle l'empreinte est refusee AU PLAN."
  type        = number
  default     = 8
}
