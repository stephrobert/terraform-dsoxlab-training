# A COMPLETER. Chaque valeur doit venir de l'enumere declare dans
# `questionnaire.tf` : une reponse hors liste est refusee au plan.

reponses = {
  # Un `terraform workspace new` cree quoi, exactement ?
  ce_que_nomme_un_workspace_cli = "???"

  # Et un workspace HCP Terraform ?
  ce_que_nomme_un_workspace_hcp = "???"

  # Quand on travaille avec HCP Terraform, ou sont declarees les variables
  # d'entree d'un run ?
  ou_vivent_les_variables = "???"

  # Pourquoi `name` et `tags` ne peuvent-ils pas figurer ensemble ?
  ce_qui_exclut_name_et_tags = "???"

  # Des trois fautes de `nomme/`, lesquelles `terraform validate` attrape-t-il ?
  ce_que_validate_attrape = "???"
}
