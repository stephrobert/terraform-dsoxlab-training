# Fourni, complet. Ce sont ces trois valeurs que vous ferez varier.

variable "nom_de_la_vm" {
  description = "Nom du domaine libvirt."
  type        = string
  default     = "tf-lab-vm"
}

variable "memoire_mio" {
  description = "Memoire allouee, en Mio."
  type        = number
  default     = 512
}

variable "vcpu" {
  description = "Nombre de processeurs virtuels."
  type        = number
  default     = 1
}

variable "image_de_base" {
  description = "Image cloud servant de socle en copie sur ecriture."
  type        = string
  default     = "/var/tmp/dsoxlab-images/noble-server-cloudimg-amd64.img"
}
