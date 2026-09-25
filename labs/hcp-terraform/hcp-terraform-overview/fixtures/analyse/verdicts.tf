# A COMPLETER : remplacez le ??? par une expression qui qualifie CHAQUE
# situation, sans en nommer aucune.
#
# Une expression qui traiterait les cas un par un, par leur cle, ne serait pas
# une regle : elle serait une liste de reponses. Les tests ne le verraient pas,
# mais un septieme cas non plus.
#
# Le vocabulaire des verdicts, et rien d'autre :
#
#   plan_speculatif        le run ne pourra JAMAIS appliquer, quoi qu'il montre
#   planned_and_finished   le run se termine sans apply
#   apply_automatique      l'apply part sans qu'un humain confirme
#   attend_confirmation    le run s'arrete et attend une action
#   aucun_run_distant      HCP Terraform n'execute rien pour ce workspace
#
# Quatre points a trancher, et ils ne sont pas dans le meme ordre d'importance :
#
#   - un mode d'execution qui n'est pas `remote` change la nature du workspace
#     avant toute autre consideration ;
#   - deux declencheurs ne produisent que des plans speculatifs, et le reglage
#     d'auto-apply n'y peut rien ;
#   - un plan sans changement ne s'applique pas, meme en auto-apply ;
#   - tous les declencheurs ne donnent pas droit a l'auto-apply.

output "verdicts" {
  description = "Le verdict de chacune des six situations."
  value       = ???
}
