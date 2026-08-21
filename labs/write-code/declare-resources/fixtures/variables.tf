variable "etiquette" {
  description = "Étiquette du sceau. Un changement se met à jour en place."
  type        = string
  default     = "v1"
}

variable "generation" {
  description = "Génération. Un changement remplace l'hôte, et par propagation le sceau."
  type        = number
  default     = 1
}
