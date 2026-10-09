variable "prefixe" {
  description = "Préfixe des noms de machines et de disques sur l'hôte libvirt."
  type        = string
}

variable "image_de_base" {
  description = "Image cloud en lecture seule, dont chaque disque est une copie sur écriture."
  type        = string
  default     = "/var/tmp/dsoxlab-images/noble-server-cloudimg-amd64.img"
}

variable "machines" {
  description = "Les machines de l'environnement, par rôle."
  type = map(object({
    memoire_mib = number
    vcpu        = number
  }))
}
