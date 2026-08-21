variable "env" {
  description = "Environnement cible. Seuls dev, staging et prod ont un sens ici."
  type        = string
  default     = "prod"
}

variable "revision" {
  description = "Révision fonctionnelle. La faire bouger doit forcer un remplacement."
  type        = number
  default     = 1
}

variable "message" {
  description = "Contenu du journal applicatif."
  type        = string
  default     = "v1"
}

variable "permissions" {
  description = "Permissions POSIX du journal, au format octal sur quatre chiffres."
  type        = string
  default     = "0644"
}
