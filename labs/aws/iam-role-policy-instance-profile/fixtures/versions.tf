# Fourni, complet. La configuration du provider n'est pas l'objet de ce lab.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region     = var.aws_region
  access_key = "test"
  secret_key = "test"

  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true

  endpoints {
    ec2 = var.emulateur_endpoint
    iam = var.emulateur_endpoint
    sts = var.emulateur_endpoint
    s3  = var.emulateur_endpoint
  }
}
