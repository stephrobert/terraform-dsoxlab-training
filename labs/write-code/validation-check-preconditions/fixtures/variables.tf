variable "nom_projet" {
  type    = string
  default = "lab-conditions"

  # ??? niveau 1 (validation de variable) : refuser AVANT le plan un nom vide
  #     ou de plus de 20 caracteres. condition ET error_message a remplir.
  validation {
    condition     = ???
    error_message = ???
  }
}

variable "taille_lot" {
  type    = number
  default = 2

  # ??? validation CROISEE : taille_lot ne doit pas depasser taille_max. Une
  #     validation peut referencer une AUTRE variable (Terraform >= 1.9).
  validation {
    condition     = ???
    error_message = ???
  }
}

variable "taille_max" {
  type    = number
  default = 5
}
