variable "prefixe" {
  type        = string
  description = "Prefixe de l'etiquette."

  validation {
    condition     = length(var.prefixe) >= 3
    error_message = "Le prefixe doit contenir au moins 3 caracteres."
  }
}

variable "suffixe" {
  type        = string
  description = "Suffixe facultatif, ajoute derriere un tiret."
  default     = ""
}

variable "majuscules" {
  type        = bool
  description = "Passe l'etiquette en majuscules."
  default     = false
}
