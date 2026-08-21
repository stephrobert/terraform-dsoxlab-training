variable "services" {
  type        = list(string)
  description = "Les services a materialiser, un fichier par service."
  default     = ["web", "api", "cache"]
}

variable "workers" {
  type        = number
  description = "Nombre de workers interchangeables a generer."
  default     = 3
}

variable "rapport" {
  type        = bool
  description = "Genere (ou non) le fichier rapport optionnel."
  default     = false
}
