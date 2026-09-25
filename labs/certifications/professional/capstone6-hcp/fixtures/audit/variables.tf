# Fourni. A NE PAS MODIFIER.
#
# Six situations, et chacune croise DEUX sous-objectifs de l'objectif 6. C'est
# ce qui distingue un capstone des sept labs de la section : pris un par un,
# chaque champ se traite par un reflexe appris ; ensemble, ils s'annulent ou se
# renforcent, et il faut trancher dans le bon ordre.

variable "situations" {
  description = "Six runs decrits, a qualifier."

  type = map(object({
    # 6a : ce qui declenche le run.
    #   pull_request, commit_sur_la_branche, cli_terraform_apply, run_trigger
    declencheur = string

    # 6a : le reglage du workspace.
    auto_apply = bool

    # 6b : remote, local, agent.
    mode_execution = string

    # 6a : le plan porte-t-il des changements ?
    changements = bool

    # 6d : une policy est-elle configuree, et echoue-t-elle ?
    #   aucune, advisory_en_echec, mandatory_en_echec
    policy = string

    # 6d : le policy set autorise-t-il l'override, et l'auteur a-t-il la
    # permission ? Les deux sont necessaires.
    override_autorise  = bool
    permission_override = bool
  }))
}
