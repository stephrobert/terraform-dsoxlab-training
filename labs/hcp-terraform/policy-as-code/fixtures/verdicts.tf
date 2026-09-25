# A COMPLETER.
#
# Pour chaque run, dire s'il POURSUIT, s'il est BLOQUE mais surchargeable, ou
# s'il est BLOQUE sans recours.
#
# Le piege, et il fait tomber les candidats : ce n'est PAS le seul niveau
# d'enforcement qui tranche. Un `hard-mandatory` n'est pas indepassable.
#
# Trois valeurs admises, exactement :
#
#   "poursuit"               la policy echoue, le run continue
#   "bloque_surchargeable"   le run est arrete, quelqu'un peut passer outre
#   "bloque"                 le run est arrete, personne ne peut rien
#
# Chaque situation porte tout ce qu'il faut pour decider : le niveau, ce que le
# POLICY SET autorise, et ce que l'utilisateur DETIENT.

locals {
  verdicts = {
    for nom, cas in var.situations : nom => ???
  }
}

output "verdicts" {
  description = "Un verdict par run."
  value       = local.verdicts
}
