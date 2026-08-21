variable "services" {
  type        = set(string)
  description = "Les services a materialiser (cles NON sensibles)."
  default     = ["web", "db"]
}

variable "db_password" {
  type        = string
  description = "Mot de passe, sensible."
  sensitive   = true
  default     = "s3cr3t-demo"
}
