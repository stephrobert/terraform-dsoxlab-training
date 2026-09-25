# Fourni. A NE PAS MODIFIER.
#
# Le type des six situations. Chacune porte tout ce qu'il faut pour trancher, et
# rien de plus : si un champ vous semble inutile pour un cas, c'est peut-etre
# qu'un autre champ le rend sans objet.

variable "situations" {
  description = "Six runs decrits, a qualifier."

  type = map(object({
    # pull_request, commit_sur_la_branche, cli_terraform_plan,
    # cli_terraform_apply, api, run_trigger
    declencheur = string

    # Le reglage du workspace.
    auto_apply = bool

    # remote, local, agent
    mode_execution = string

    # Le plan porte-t-il des changements ?
    changements = bool

    # L'auteur du run detient-il la permission d'appliquer ?
    permission_apply = bool
  }))
}
