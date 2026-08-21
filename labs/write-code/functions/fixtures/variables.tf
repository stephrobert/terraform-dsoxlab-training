# Ce fichier est COMPLET. Ne le modifiez pas : les tests s'appuient sur ces
# valeurs exactes.

variable "environments_csv" {
  type    = string
  default = "prod,dev,prod,staging"
}

variable "tags" {
  type    = map(string)
  default = { projet = "demo", equipe = "devops" }
}

variable "environment" {
  type    = string
  default = "qa"
}

variable "memory_mib" {
  type    = number
  default = 1536
}
