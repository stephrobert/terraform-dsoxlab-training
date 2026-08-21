terraform {
  # Le provider vault en 5.x apporte les ressources ephemeres et les arguments
  # write-only (data_json_wo). Elles exigent Terraform 1.11 ou plus recent.
  required_version = ">= 1.11.0"

  required_providers {
    vault = {
      source  = "hashicorp/vault"
      version = ">= 5.0"
    }
  }
}
