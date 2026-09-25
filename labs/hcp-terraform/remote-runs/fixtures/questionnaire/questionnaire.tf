# Fourni, complet. A NE PAS MODIFIER.
#
# Les blocs `validation` refusent tout mot hors de l'enumere : une reponse mal
# orthographiee est refusee AU PLAN, avec un message qui dit quoi ecrire.

variable "reponses" {
  description = "Les cinq reponses sur les trois workflows de run."

  type = object({
    workflow_sans_remote_apply         = string
    ce_qu_un_run_cli_envoie            = string
    d_ou_viennent_les_variables_en_cli = string
    workflow_pour_le_non_interactif    = string
    fichier_qui_exclut_de_l_upload     = string
  })

  validation {
    condition = contains(
      ["ui_vcs", "api", "cli"],
      var.reponses.workflow_sans_remote_apply
    )
    error_message = "Attendu ui_vcs, api ou cli."
  }

  validation {
    condition = contains(
      ["une_archive_du_repertoire_local", "un_lien_vers_le_depot", "le_state_courant"],
      var.reponses.ce_qu_un_run_cli_envoie
    )
    error_message = "Attendu une_archive_du_repertoire_local, un_lien_vers_le_depot ou le_state_courant."
  }

  validation {
    condition = contains(
      ["du_workspace", "du_poste", "du_depot"],
      var.reponses.d_ou_viennent_les_variables_en_cli
    )
    error_message = "Attendu du_workspace, du_poste ou du_depot."
  }

  validation {
    condition = contains(
      ["ui_vcs", "api", "cli"],
      var.reponses.workflow_pour_le_non_interactif
    )
    error_message = "Attendu ui_vcs, api ou cli."
  }

  validation {
    condition = contains(
      [".terraformignore", ".gitignore", ".terraform.lock.hcl"],
      var.reponses.fichier_qui_exclut_de_l_upload
    )
    error_message = "Attendu .terraformignore, .gitignore ou .terraform.lock.hcl."
  }
}

output "reponses" {
  description = "Les reponses republiees, pour que les tests les lisent."
  value       = var.reponses
}
