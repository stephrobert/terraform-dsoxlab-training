# A COMPLETER : les onze etapes d'un run, DANS L'ORDRE.
#
# Elles sont donnees ci-dessous par ordre alphabetique, ce qui n'apprend rien.
# L'ordre reel se lit dans la documentation des run states, et deux d'entre
# elles encadrent l'estimation de cout : ce n'est pas un detail, c'est ce qui
# decide si une regle peut lire un cout ou non.
#
#   apply, cost_estimation, fetching, opa_policy_check, pending,
#   post_apply, post_plan, plan, pre_apply, pre_plan, sentinel_policy_check

output "etapes_du_run" {
  description = "Les onze etapes d'un run HCP Terraform, dans l'ordre."
  value       = ???
}
