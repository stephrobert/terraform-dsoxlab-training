# A COMPLETER : trois `???`, qui se lisent et ne se devinent pas.

output "gouvernance" {
  description = "Trois faits qui croisent les sous-objectifs de l'objectif 6."

  value = {
    # Ce qui decide qu'une policy en echec peut etre surchargee. Un mot parmi :
    #   le_niveau_d_enforcement, le_reglage_du_policy_set_et_la_permission,
    #   la_permission_seule
    ce_qui_autorise_un_override = ???

    # Un workspace dont le mode d'execution vaut `local` : que devient
    # l'evaluation des policies ? Un mot parmi :
    #   elles_s_executent_quand_meme, elles_ne_s_executent_pas,
    #   elles_s_executent_sur_le_poste
    policies_en_mode_local = ???

    # Ou vivent les identifiants qu'un run emploie pour parler a un cloud ?
    # Un mot parmi :
    #   le_depot, des_variables_d_environnement_du_workspace, le_state
    ou_vivent_les_identifiants = ???
  }
}
