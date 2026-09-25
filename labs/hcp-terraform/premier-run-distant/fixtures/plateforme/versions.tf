# Fourni. A NE PAS MODIFIER.
#
# Le provider `tfe` pilote HCP Terraform lui-meme : organisations, projets,
# workspaces, variables, equipes. C'est l'infrastructure as code appliquee a la
# plateforme qui execute votre infrastructure as code.
#
# Version epinglee sur la 0.81, publiee le 2026-09-15, releve du registre le
# 2026-09-25.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    tfe = {
      source  = "hashicorp/tfe"
      version = "~> 0.81"
    }
  }
}

# Aucun bloc `provider` : le provider `tfe` lit le meme jeton que la CLI, dans
# `~/.terraform.d/credentials.tfrc.json` ou dans `TF_TOKEN_app_terraform_io`.
# Une configuration qui recoit ses identifiants plutot que de les contenir,
# exactement comme le lab `shared-credentials` l'a etabli.
