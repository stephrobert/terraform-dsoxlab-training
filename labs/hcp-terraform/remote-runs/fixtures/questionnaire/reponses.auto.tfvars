# A COMPLETER. Chaque valeur doit venir de l'enumere declare dans
# `questionnaire.tf` : une reponse hors liste est refusee au plan.

reponses = {
  # Dans quel workflow un remote apply est-il impossible, parce que la source
  # de verite du workspace est ailleurs ?
  workflow_sans_remote_apply = "???"

  # Que la CLI envoie-t-elle a HCP Terraform quand elle declenche un run ?
  ce_qu_un_run_cli_envoie = "???"

  # Un run lance depuis la CLI prend son CODE dans le repertoire local. Et ses
  # VALEURS de variables, d'ou viennent-elles ?
  d_ou_viennent_les_variables_en_cli = "???"

  # Quel workflow HashiCorp recommande-t-il pour un environnement non
  # interactif, une chaine d'integration continue par exemple ?
  workflow_pour_le_non_interactif = "???"

  # Quel fichier permet d'exclure des fichiers de ce qui est envoye ?
  fichier_qui_exclut_de_l_upload = "???"
}
