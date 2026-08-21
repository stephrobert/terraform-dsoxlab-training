terraform {
  required_version = ">= 1.8"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }

    # ??? Il manque ici la declaration du provider INTEGRE `terraform`,
    #     sans laquelle l'appel `provider::terraform::encode_tfvars` echoue
    #     sur « Unknown provider ». Sa source est terraform.io/builtin/terraform.
    #     Pensez a relancer `terraform init` apres l'avoir ajoute.
  }
}
