# A COMPLETER.
#
# Trois affirmations sur HCP Terraform, a etablir. Elles se lisent dans la
# documentation officielle, elles ne se devinent pas.

locals {
  # A COMPLETER : les niveaux d'enforcement de CHAQUE framework, dans l'ordre
  # du plus faible au plus fort.
  #
  # Les trois frameworks n'ont pas le meme nombre de niveaux, et ils ne les
  # nomment pas pareil : c'est precisement ce qui se confond.
  niveaux_par_framework = ???

  # A COMPLETER : ce qui distingue les policy CHECKS des policy EVALUATIONS.
  #
  #   framework_unique      le seul framework qui s'execute dans les checks
  #   version_maximale      la version de ce framework au dela de laquelle les
  #                         checks ne suivent plus
  #   voit_le_cout          les checks peuvent-ils lire l'estimation de cout ?
  #
  # Indice de lecture : les checks s'executent APRES l'estimation de cout, les
  # evaluations juste AVANT. Cela decide de ce que chacun peut voir.
  policy_checks = ???

  # A COMPLETER : ce que l'edition Free autorise.
  #
  #   policy_sets           combien de policy sets
  #   policies_par_set      combien de policies dedans
  #   connexion_vcs         peut-on y brancher un depot ?
  free_tier = ???
}

output "niveaux_par_framework" {
  description = "Les niveaux d'enforcement de chaque framework."
  value       = local.niveaux_par_framework
}

output "policy_checks" {
  description = "Ce qui distingue les policy checks des policy evaluations."
  value       = local.policy_checks
}

output "free_tier" {
  description = "Ce que l'edition Free autorise en policy as code."
  value       = local.free_tier
}
