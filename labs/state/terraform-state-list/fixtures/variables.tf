# Les cinq reponses attendues. Elles sont alimentees par reponses.auto.tfvars,
# le seul fichier a remplir. Ne rien changer ici.

variable "adresse_worker" {
  description = "Adresse de l'instance de random_pet.worker portant l'id publie."
  type        = string
}

variable "adresse_service" {
  description = "Adresse de l'instance de random_pet.service portant l'id publie."
  type        = string
}

variable "adresse_archive" {
  description = "Adresse, qualifiee par le module, de l'archive portant l'id publie."
  type        = string
}

variable "adresse_data_module" {
  description = "Adresse complete de la data source declaree dans le module."
  type        = string
}

variable "nombre_managees" {
  description = "Nombre d'instances en mode managed dans le state, modules inclus."
  type        = number
}
