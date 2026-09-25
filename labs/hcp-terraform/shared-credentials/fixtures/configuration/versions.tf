# A CORRIGER.
#
# Ce provider porte ses identifiants EN DUR. C'est le defaut que ce lab traite,
# et il est plus courant qu'on ne croit : la valeur est courte, elle marche, et
# elle part dans le depot avec le reste.
#
# HCP Terraform ne fonctionne pas ainsi. Il pose les identifiants dans
# l'ENVIRONNEMENT du run, juste avant le plan ou l'apply, et les jette avec cet
# environnement a la fin. La configuration, elle, n'en sait rien : elle doit
# etre ecrite pour les recevoir, pas pour les contenir.
#
# Le provider AWS lit `AWS_ACCESS_KEY_ID` et `AWS_SECRET_ACCESS_KEY` dans son
# environnement quand la configuration ne lui donne rien.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 6.0, < 7.0"
    }
  }
}

provider "aws" {
  region = var.aws_region

  # A RETIRER, toutes les deux.
  access_key = "AKIAIOSFODNN7EXAMPLE"
  secret_key = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

  # Fourni : l'emulateur ne verifie pas les identifiants, mais le provider
  # exige d'en trouver. Sans aucun, il repond « No valid credential sources
  # found » et ne plane meme pas.
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    ec2 = var.emulateur_endpoint
  }
}
