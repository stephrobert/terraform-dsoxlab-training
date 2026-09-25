# Fourni. A NE PAS MODIFIER.

variable "organisation" {
  description = <<-TXT
    Le nom de VOTRE organisation HCP Terraform.

    Il figure dans l'URL quand vous etes connecte, `app.terraform.io/app/<ici>`,
    et dans le selecteur en haut de l'interface.
  TXT

  type = string

  validation {
    condition     = var.organisation != "???" && trimspace(var.organisation) != ""
    error_message = "Renseignez votre organisation dans organisation.auto.tfvars."
  }
}

variable "projet" {
  description = "Le projet a creer."
  type        = string
  default     = "formation-terraform"
}

variable "workspace" {
  description = "Le workspace a creer."
  type        = string
  default     = "premier-run-distant"
}

variable "message" {
  description = <<-TXT
    La valeur posee comme variable DU WORKSPACE.

    Elle ne sera pas envoyee avec votre configuration : c'est HCP Terraform qui
    la fournira au run, ce que le lab `hcp-workspaces` a etabli en theorie et
    que celui-ci vous fait constater.
  TXT

  type    = string
  default = "pose-dans-le-workspace"
}
