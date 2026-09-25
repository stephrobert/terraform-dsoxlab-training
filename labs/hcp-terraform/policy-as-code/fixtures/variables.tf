# Fourni, complet. A ne pas modifier.

variable "situations" {
  description = "Les runs a qualifier, decrits par framework, niveau et droits."

  type = map(object({
    framework                          = string
    niveau                             = string
    policy_en_echec                    = bool
    override_autorise_par_le_policy_set = bool
    detient_manage_policy_overrides    = bool
  }))
}

variable "_commentaire" {
  description = "Present pour que le fichier de situations reste lisible."
  type        = string
  default     = ""
}
