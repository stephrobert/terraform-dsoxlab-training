# Fourni, complet. A NE PAS MODIFIER.
#
# Les blocs `validation` refusent tout mot hors de l'enumere : une reponse mal
# orthographiee est refusee AU PLAN, avec un message qui dit quoi ecrire.

variable "reponses" {
  description = "Les cinq reponses sur les projets, les equipes et leurs droits."

  type = object({
    ce_qui_tranche_entre_deux_niveaux = string
    qui_peut_declencher_un_plan_vcs   = string
    duree_de_vie_du_jeton_run_task    = string
    role_entre_lecture_et_ecriture    = string
    role_entre_ecriture_et_admin      = string
  })

  validation {
    condition = contains(
      ["le_plus_permissif", "le_plus_specifique", "le_dernier_pose"],
      var.reponses.ce_qui_tranche_entre_deux_niveaux
    )
    error_message = "Attendu le_plus_permissif, le_plus_specifique ou le_dernier_pose."
  }

  validation {
    condition = contains(
      [
        "quiconque_peut_fusionner_dans_la_branche",
        "les_membres_de_l_organisation_seulement",
        "les_administrateurs_du_workspace_seulement",
      ],
      var.reponses.qui_peut_declencher_un_plan_vcs
    )
    error_message = "Attendu quiconque_peut_fusionner_dans_la_branche, les_membres_de_l_organisation_seulement ou les_administrateurs_du_workspace_seulement."
  }

  validation {
    condition = contains(
      ["dix_minutes", "une_heure", "le_temps_du_run"],
      var.reponses.duree_de_vie_du_jeton_run_task
    )
    error_message = "Attendu dix_minutes, une_heure ou le_temps_du_run."
  }

  validation {
    condition = contains(
      ["plan", "maintenance", "aucun"],
      var.reponses.role_entre_lecture_et_ecriture
    )
    error_message = "Attendu plan, maintenance ou aucun."
  }

  validation {
    condition = contains(
      ["plan", "maintenance", "aucun"],
      var.reponses.role_entre_ecriture_et_admin
    )
    error_message = "Attendu plan, maintenance ou aucun."
  }
}

output "reponses" {
  description = "Les reponses republiees, pour que les tests les lisent."
  value       = var.reponses
}
