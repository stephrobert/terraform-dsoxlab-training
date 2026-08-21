# Le BOOTSTRAP : il cree le bucket qui accueillera le state des autres
# configurations. COMPLET, a appliquer tel quel.
#
# Son propre state reste LOCAL, par necessite : le backend doit exister avant
# qu'on puisse s'en servir. Une configuration ne peut pas ranger son state dans
# un bucket qu'elle est en train de creer.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 5.0"
    }
  }
}

provider "aws" {
  region     = "eu-west-3"
  access_key = "test"
  secret_key = "test"

  # Les arguments qui font parler ce provider a un emulateur local plutot qu'a
  # AWS. Le support du S3 compatible est annonce « best effort » par HashiCorp.
  s3_use_path_style           = true
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  skip_region_validation      = true

  endpoints {
    s3 = "http://localhost:14566"
  }
}

resource "aws_s3_bucket" "state" {
  bucket = "tf-state-lab"
}

# Le versioning n'est pas decoratif : c'est lui qui permet de revenir a une
# version anterieure du state apres une operation malheureuse.
resource "aws_s3_bucket_versioning" "state" {
  bucket = aws_s3_bucket.state.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_s3_bucket_public_access_block" "state" {
  bucket = aws_s3_bucket.state.id

  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

output "bucket" {
  description = "Nom du bucket de state."
  value       = aws_s3_bucket.state.id
}
