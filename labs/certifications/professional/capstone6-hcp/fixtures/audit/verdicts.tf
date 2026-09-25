# A COMPLETER : un `???`, et c'est le coeur du capstone.
#
# Chaque situation croise DEUX sous-objectifs. Pris separement, chaque champ se
# traite par un reflexe que les sept labs de la section ont installe. Ensemble,
# ils se renforcent ou s'annulent, et l'ordre dans lequel on les regarde decide
# du resultat.
#
# Le vocabulaire, et rien d'autre :
#
#   aucun_run_distant      HCP Terraform n'execute rien pour ce workspace
#   plan_speculatif        le run ne pourra JAMAIS appliquer
#   planned_and_finished   le run se termine sans apply
#   bloque                 une policy arrete le run, sans recours
#   bloque_surchargeable   une policy l'arrete, mais quelqu'un peut passer outre
#   apply_automatique      l'apply part sans qu'un humain confirme
#   attend_confirmation    le run s'arrete et attend une action
#
# Cinq regles a ordonner, et elles ne commutent pas :
#
#   - un mode d'execution qui n'est ni `remote` ni `agent` change la nature du
#     workspace avant toute autre consideration : aucune policy ne s'execute,
#     aucun run ne part ;
#   - une pull request ne produit qu'un plan speculatif, et une policy en echec
#     n'y change rien : il n'y a rien a bloquer, le run ne pouvait pas appliquer ;
#   - un plan sans changement termine le run. Attention toutefois : la
#     documentation conditionne cette fin a l'absence de policy. Quand une
#     policy est configuree, le run poursuit vers sa verification ;
#   - une policy `advisory` n'arrete jamais rien, quel que soit le reste ;
#   - une policy `mandatory` en echec bloque, et l'override demande DEUX choses,
#     le reglage du policy set ET la permission de l'auteur. Le niveau seul ne
#     decide de rien.
#
# Et pour finir, l'auto-apply : le reglage ne suffit pas, le declencheur doit y
# donner droit.

locals {
  # Les declencheurs qui ne produisent qu'un plan speculatif.
  declencheurs_speculatifs = ["pull_request", "cli_terraform_plan"]

  # Ceux qui donnent droit a l'auto-apply. Un `run_trigger` n'en fait pas
  # partie : « Some plans can't be auto-applied, like plans queued by run
  # triggers or by users without permission to apply runs. »
  declencheurs_auto_appliquables = [
    "commit_sur_la_branche",
    "cli_terraform_apply",
    "api",
  ]
}

output "verdicts" {
  description = "Le verdict de chacune des six situations."
  value       = ???
}
