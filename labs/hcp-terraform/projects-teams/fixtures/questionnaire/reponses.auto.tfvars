# A COMPLETER. Chaque valeur doit venir de l'enumere declare dans
# `questionnaire.tf` : une reponse hors liste est refusee au plan.

reponses = {
  # Une equipe detient un droit au niveau organisation et un autre au niveau
  # workspace. Lequel des deux s'applique ?
  ce_qui_tranche_entre_deux_niveaux = "???"

  # Un workspace est relie a un depot. Qui peut, en pratique, y faire partir un
  # plan ?
  qui_peut_declencher_un_plan_vcs = "???"

  # Combien de temps vit le jeton d'acces qu'une run task recoit ?
  duree_de_vie_du_jeton_run_task = "???"

  # Dans l'echelle des roles de WORKSPACE, quel role se situe entre la lecture
  # et l'ecriture ? Repondez `aucun` s'il n'y en a pas.
  role_entre_lecture_et_ecriture = "???"

  # Dans l'echelle des roles de PROJET, quel role se situe entre l'ecriture et
  # l'administration ? Repondez `aucun` s'il n'y en a pas.
  role_entre_ecriture_et_admin = "???"
}
