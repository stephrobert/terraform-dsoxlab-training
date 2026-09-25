# Fourni, complet. A ne pas modifier.

variable "cas" {
  description = "Pour chaque cas, les sources renseignees et leur valeur."
  type        = map(map(string))
}

variable "duel_lexical" {
  description = <<-TEXTE
    Deux variable sets de portee ET de proprietaire identiques, qui posent la
    meme cle. Rien dans la precedence ne les separe : c'est l'ordre
    lexicographique de leur NOM qui tranche.
  TEXTE
  type        = map(string)

  default = {
    "equipe-plateforme" = "plateforme"
    "equipe-donnees"    = "donnees"
  }
}

variable "sentinelle" {
  description = "Ce que resout un cas dont aucune source n'est renseignee."
  type        = string
  default     = "default_hcl"
}
