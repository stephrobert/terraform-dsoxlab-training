# Les entrees du module.
#
# ??? : chaque variable d'un module reutilisable porte une `description`. C'est
# la seule documentation que voit l'appelant, et le JSON de configuration
# l'expose : les tests la lisent la.
#
# Aucune de ces trois variables n'a de `default`, et c'est voulu : sans valeur
# par defaut, une variable est OBLIGATOIRE, et l'appelant ne peut pas oublier de
# la fournir.

variable "nom" {
  type = string
}

variable "cible" {
  type = string
}

variable "retention" {
  type = number
}
