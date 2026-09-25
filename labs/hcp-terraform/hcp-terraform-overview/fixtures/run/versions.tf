# Fourni. A NE PAS MODIFIER.
#
# Le provider `local` suffit : ce lab n'a rien a provisionner, il fait jouer un
# run en deux temps.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}
