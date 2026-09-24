# Fourni, complet.

variable "nom_du_reseau" {
  description = "Nom du reseau virtuel. Le rapport le consomme, LUI AUSSI."
  type        = string
  default     = "tf-lab-reseau"
}

variable "passerelle" {
  type    = string
  default = "10.77.0.1"
}

variable "masque" {
  type    = string
  default = "255.255.255.0"
}
