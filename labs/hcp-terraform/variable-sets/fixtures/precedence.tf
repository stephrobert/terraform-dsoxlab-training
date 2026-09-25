# A COMPLETER : la table de precedence, du PLUS PRIORITAIRE au moins.
#
# Quinze entrees, et onze valent `"???"`. Les quatre deja posees sont des
# ANCRES : elles interdisent de deviner la table en la faisant tourner d'un
# cran, ce qui est l'erreur la plus economique et la plus fausse.
#
# Les quinze identifiants admis sont dans `VOCABULAIRE.md`. N'en inventez aucun.
#
# L'inversion a garder en tete : chez les sets NORMAUX la portee la plus etroite
# gagne, chez les PRIORITAIRES c'est la plus large.

locals {
  ordre = [
    "cli_var",          # ancre : rien ne bat la ligne de commande
    "tf_var_env",       # ancre
    "???",
    "???",
    "???",
    "???",
    "???",
    "workspace",        # ancre : au milieu, entre les deux familles de sets
    "???",
    "???",
    "???",
    "???",
    "???",
    "???",
    "terraform_tfvars", # ancre : rien ne perd contre lui
  ]
}

output "ordre_precedence" {
  description = "Les quinze sources, du plus prioritaire au moins."
  value       = local.ordre
}
