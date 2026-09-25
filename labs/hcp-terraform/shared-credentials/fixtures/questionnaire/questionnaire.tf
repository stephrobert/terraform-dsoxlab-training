# Fourni, complet. A NE PAS MODIFIER.
#
# Les blocs `validation` refusent tout mot hors de l'enumere : une reponse mal
# orthographiee est refusee AU PLAN, avec un message qui dit quoi ecrire.

variable "reponses" {
  description = "Les cinq reponses sur les identifiants de provider."

  type = object({
    ce_que_sensible_protege        = string
    ce_que_hcp_envoie_au_cloud     = string
    ce_qui_verifie_ce_jeton        = string
    duree_de_vie_des_identifiants  = string
    ou_vivent_les_identifiants_hcp = string
  })

  validation {
    condition = contains(
      ["l_affichage_seulement", "l_affichage_et_le_state", "tout_le_cycle"],
      var.reponses.ce_que_sensible_protege
    )
    error_message = "Attendu l_affichage_seulement, l_affichage_et_le_state ou tout_le_cycle."
  }

  validation {
    condition = contains(
      ["un_workload_identity_token", "la_cle_privee_du_workspace", "les_identifiants_statiques"],
      var.reponses.ce_que_hcp_envoie_au_cloud
    )
    error_message = "Attendu un_workload_identity_token, la_cle_privee_du_workspace ou les_identifiants_statiques."
  }

  validation {
    condition = contains(
      ["la_cle_publique_de_hcp", "le_mot_de_passe_du_compte", "le_certificat_du_workspace"],
      var.reponses.ce_qui_verifie_ce_jeton
    )
    error_message = "Attendu la_cle_publique_de_hcp, le_mot_de_passe_du_compte ou le_certificat_du_workspace."
  }

  validation {
    condition = contains(
      ["le_temps_du_run", "trente_jours", "jusqu_a_rotation_manuelle"],
      var.reponses.duree_de_vie_des_identifiants
    )
    error_message = "Attendu le_temps_du_run, trente_jours ou jusqu_a_rotation_manuelle."
  }

  validation {
    condition = contains(
      ["des_variables_d_environnement", "un_fichier_tfvars", "le_code_de_la_configuration"],
      var.reponses.ou_vivent_les_identifiants_hcp
    )
    error_message = "Attendu des_variables_d_environnement, un_fichier_tfvars ou le_code_de_la_configuration."
  }
}

output "reponses" {
  description = "Les reponses republiees, pour que les tests les lisent."
  value       = var.reponses
}
