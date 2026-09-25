# A COMPLETER : trois faits qui se lisent, et qui ne se devinent pas.

output "faits" {
  description = "Trois faits sur la file de runs et les modes d'execution."

  value = {
    # Un workspace traite ses runs dans l'ordre, et un run en cours bloque les
    # suivants. Deux operations font exception et peuvent avancer a tout
    # moment. Nommez-les, dans cet ordre alphabetique :
    #
    #   planification_des_saved_plan_runs, runs_plan_only
    operations_qui_ne_bloquent_pas_la_file = ???

    # Les run tasks peuvent s'executer a plusieurs etapes. A UNE seule d'entre
    # elles, un echec n'arrete pas le run, et la raison tient en quelques mots.
    # Donnez le nom de l'etape, tel qu'il figure dans `etapes_du_run`.
    etape_ou_un_echec_n_arrete_plus_le_run = ???

    # Un workspace dont le mode d'execution vaut `local` n'execute plus rien
    # dans HCP Terraform. Que continue-t-il de fournir ? Un mot parmi :
    #
    #   le_stockage_du_state, l_estimation_de_cout, les_notifications
    ce_que_fournit_encore_un_workspace_local = ???
  }
}
