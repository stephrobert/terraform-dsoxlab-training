# Fourni. A NE PAS MODIFIER.
#
# Six equipes, chacune decrite par ce qu'elle detient aux TROIS niveaux ou une
# permission peut etre posee : l'organisation, le projet, le workspace.
#
# Un niveau peut valoir `aucun` : l'equipe n'a rien recu a ce niveau-la.

variable "equipes" {
  description = "Six equipes, et leurs droits aux trois niveaux."

  type = map(object({
    # Permission d'ORGANISATION, parmi :
    #   aucun, vue_de_tous_les_workspaces, gestion_de_tous_les_workspaces
    organisation = string

    # Role de PROJET, parmi :
    #   aucun, lecture, ecriture, maintenance, administration
    projet = string

    # Role de WORKSPACE, parmi :
    #   aucun, lecture, plan, ecriture, administration
    workspace = string
  }))
}
