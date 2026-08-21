# Piege : cette variable existe mais NE PEUT PAS servir dans le bloc backend. Un
# `backend "local" { path = var.chemin_state }` fait echouer init sur
# « Variables not allowed ». Le bloc backend n'accepte aucune valeur nommee.
variable "chemin_state" {
  type    = string
  default = "etat/dev/terraform.tfstate"
}
