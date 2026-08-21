variable "env_name" {
  description = "Nom de l'environnement servi. Aucun default : c'est le garde-fou."
  type        = string
}

variable "disk_size_gb" {
  description = "Taille du volume, en Go. Aucun default non plus."
  type        = number
}

variable "retention_jours" {
  description = "Duree de retention des sauvegardes, en jours."
  type        = number
  default     = 7
}

variable "base_image" {
  description = "Image de base, commune a tous les environnements."
  type        = ???
}

variable "tags" {
  description = "Etiquettes communes, en paires cle/valeur."
  type        = ???
}
