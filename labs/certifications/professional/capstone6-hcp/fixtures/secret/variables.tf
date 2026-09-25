# Fourni. A NE PAS MODIFIER.

variable "jeton_de_run" {
  description = <<-TXT
    Le jeton qu'un run distant presenterait a un service tiers.

    Marque `sensitive`, ce qui fait exactement une chose : empecher Terraform de
    l'AFFICHER. La section l'a mesure, et c'est la moitie du piege.
  TXT

  type      = string
  sensitive = true
}
