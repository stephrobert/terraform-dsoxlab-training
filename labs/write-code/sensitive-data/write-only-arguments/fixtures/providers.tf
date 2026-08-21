# Le provider parle a Floci, l'emulateur AWS local, jamais a un vrai compte.
# Identifiants factices, appels rediriges par endpoints vers Floci, et
# validations desactivees (Floci n'implemente ni STS ni IMDS). Bloc complet :
# rien a modifier ici, l'exercice porte sur la ressource, pas sur le provider.
provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_requesting_account_id  = true
  skip_metadata_api_check     = true

  endpoints {
    ssm = var.floci_endpoint
  }
}
