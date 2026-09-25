# Fourni, complet. A NE PAS MODIFIER.
#
# Les blocs `validation` refusent tout mot hors de l'enumere : une reponse mal
# orthographiee est refusee AU PLAN, avec un message qui dit quoi ecrire.

variable "reponses" {
  description = "Les cinq reponses, a poser dans reponses.auto.tfvars."

  type = object({
    ce_que_nomme_un_workspace_cli  = string
    ce_que_nomme_un_workspace_hcp  = string
    ou_vivent_les_variables        = string
    ce_qui_exclut_name_et_tags     = string
    ce_que_validate_attrape        = string
  })

  validation {
    condition = contains(
      ["un_state", "une_execution", "un_projet"],
      var.reponses.ce_que_nomme_un_workspace_cli
    )
    error_message = "Attendu un_state, une_execution ou un_projet."
  }

  validation {
    condition = contains(
      ["un_state", "une_execution", "un_projet"],
      var.reponses.ce_que_nomme_un_workspace_hcp
    )
    error_message = "Attendu un_state, une_execution ou un_projet."
  }

  validation {
    condition = contains(
      ["le_repertoire", "le_workspace_hcp", "le_fichier_tfvars"],
      var.reponses.ou_vivent_les_variables
    )
    error_message = "Attendu le_repertoire, le_workspace_hcp ou le_fichier_tfvars."
  }

  validation {
    condition = contains(
      ["deux_strategies", "une_limite_de_taille", "une_depreciation"],
      var.reponses.ce_qui_exclut_name_et_tags
    )
    error_message = "Attendu deux_strategies, une_limite_de_taille ou une_depreciation."
  }

  validation {
    condition = contains(
      ["les_trois_fautes", "le_conflit_backend_seul", "aucune"],
      var.reponses.ce_que_validate_attrape
    )
    error_message = "Attendu les_trois_fautes, le_conflit_backend_seul ou aucune."
  }
}

output "reponses" {
  description = "Les reponses republiees, pour que les tests les lisent."
  value       = var.reponses
}
