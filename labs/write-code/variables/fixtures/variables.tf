variable "env" {
  type = string

  # ??? : refuser toute valeur hors de "dev", "staging", "prod", et le faire
  # AVANT tout appel de provider (au plan). Remplacez ce ??? par le bloc adapte.
  ???
}

variable "nodes" {
  # ??? : une map d'objets. Chaque objet a `size` (string, requis), `replicas`
  # (number, optionnel, defaut 1) et `public` (bool, optionnel, defaut false).
  # Le fichier de valeurs fournit une entree incomplete : Terraform doit la
  # completer lui-meme.
  type = ???
}

variable "retention_days" {
  type    = number
  default = 7

  # ??? : garantir qu'un `null` explicite (pose par terraform.tfvars) retombe
  # sur le defaut 7 au lieu de propager null. Remplacez ce ??? par l'argument.
  ???
}

variable "db_password" {
  type    = string
  default = "changeme-please"

  # ??? : masquer la valeur dans les affichages CLI. Remplacez ce ??? par
  # l'argument adapte (attention : ce n'est PAS une protection du secret).
  ???
}
