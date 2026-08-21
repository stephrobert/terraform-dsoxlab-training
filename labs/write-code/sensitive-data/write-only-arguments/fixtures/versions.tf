terraform {
  required_version = ">= 1.15.0"

  required_providers {
    # Les arguments write-only (suffixe _wo) sont apparus cote provider AWS en
    # 5.79. On epingle la majeure 6.x, ou ils sont stabilises.
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}
