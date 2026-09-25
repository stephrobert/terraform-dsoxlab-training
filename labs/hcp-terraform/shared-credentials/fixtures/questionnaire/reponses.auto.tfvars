# A COMPLETER. Chaque valeur doit venir de l'enumere declare dans
# `questionnaire.tf` : une reponse hors liste est refusee au plan.

reponses = {
  # Vous venez de le mesurer sur votre propre state. Que protege exactement
  # l'annotation `sensitive` ?
  ce_que_sensible_protege = "???"

  # Avec les identifiants dynamiques, que HCP Terraform envoie-t-il a la
  # plateforme cloud au debut d'un plan ou d'un apply ?
  ce_que_hcp_envoie_au_cloud = "???"

  # Et avec quoi la plateforme cloud verifie-t-elle ce que HCP lui envoie ?
  ce_qui_verifie_ce_jeton = "???"

  # Combien de temps vivent les identifiants que la plateforme renvoie ?
  duree_de_vie_des_identifiants = "???"

  # Dans un workspace HCP Terraform, ou se declarent les identifiants d'un
  # provider ?
  ou_vivent_les_identifiants_hcp = "???"
}
