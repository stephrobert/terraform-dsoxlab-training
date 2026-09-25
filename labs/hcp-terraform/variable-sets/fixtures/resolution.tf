# A COMPLETER : resoudre chaque cas.
#
# Pour chaque cas, trouver la source renseignee la PLUS PRIORITAIRE, et rendre
# son identifiant ET sa valeur.
#
# Contrainte, et c'est elle qui est controlee : parcourir `local.ordre`. Ne
# nommez AUCUN cas en dur. Les tests rejouent la configuration avec huit cas
# qu'ils generent eux-memes, et qu'aucune resolution ecrite cas par cas ne peut
# prevoir.
#
# Un cas dont aucune source n'est renseignee resout sur `var.sentinelle`, jamais
# sur `null` et jamais sur une erreur de plan.

locals {
  resolutions = ???
}

# A COMPLETER : departager deux sets que la precedence ne separe pas.
#
# Meme portee, meme proprietaire : c'est l'ordre LEXICOGRAPHIQUE de leur nom qui
# tranche, par points de code Unicode. Pas leur ordre d'apparition dans la map,
# qui n'existe pas : une map HCL n'a pas d'ordre.
locals {
  gagnant_lexical = ???
}

resource "local_file" "resultat" {
  filename = "${path.module}/resolutions.json"
  content  = jsonencode(local.resolutions)
}

output "resolutions" {
  description = "Pour chaque cas, la source retenue et sa valeur."
  value       = local.resolutions
}

output "gagnant_lexical" {
  description = "Le nom du set qui l'emporte entre deux sets identiques."
  value       = local.gagnant_lexical
}
