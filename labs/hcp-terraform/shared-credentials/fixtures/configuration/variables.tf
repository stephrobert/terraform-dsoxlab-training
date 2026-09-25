# Fourni. A NE PAS MODIFIER.

variable "aws_region" {
  description = "La region de l'emulateur."
  type        = string
  default     = "eu-west-3"
}

variable "emulateur_endpoint" {
  description = "Le point d'entree EC2 de l'emulateur."
  type        = string
  default     = "http://localhost:14566"
}

variable "jeton_de_service" {
  description = <<-TXT
    Le jeton que le service embarque doit presenter a son homologue.

    Il est marque `sensitive`, et cette annotation fait exactement une chose :
    elle empeche Terraform de l'AFFICHER. Elle ne l'empeche ni d'entrer dans le
    state, ni d'apparaitre dans un plan enregistre.
  TXT

  type      = string
  sensitive = true
}
