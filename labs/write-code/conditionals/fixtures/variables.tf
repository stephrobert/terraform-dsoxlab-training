variable "environment" {
  type    = string
  default = "dev"

  # ??? N'accepter que dev, staging ou prod.
  #     Refus attendu AVANT la generation du plan.
}

variable "backup_bucket" {
  type    = string
  default = ""

  # ??? Obligatoire (non vide) UNIQUEMENT quand environment vaut "prod".
  #     Accepte vide sinon. La condition doit donc referencer une AUTRE
  #     variable, ce qu'autorise Terraform 1.9 et plus.
}

variable "enable_second_disk" {
  type    = bool
  default = false
}

variable "memory_mib_override" {
  type    = number
  default = null
}
