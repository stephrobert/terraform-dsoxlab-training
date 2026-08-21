# Racine du projet : c'est ICI, et nulle part ailleurs, que les providers se
# configurent. CE FICHIER EST COMPLET, il n'y a rien a y changer.

terraform {
  required_version = ">= 1.7"
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
    tls    = { source = "hashicorp/tls", version = ">= 4.0" }
  }
}

# La configuration par defaut du provider local.
provider "local" {}

# Une seconde configuration du MEME provider, distinguee par son alias : les
# archives sont ecrites par celle-ci.
provider "local" {
  alias = "archive"
}

# Le provider tls, configure une seule fois, a la racine.
provider "tls" {}
