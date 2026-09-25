# Fourni, complet. A ne pas modifier.
#
# Quatre providers locaux : aucun cloud, aucune VM, aucun cout. `archive` est la
# pour son bloc `source`, repetable, que le lab fait generer par un `dynamic`.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
    null = {
      source  = "hashicorp/null"
      version = "~> 3.2"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.6"
    }
    archive = {
      source  = "hashicorp/archive"
      version = "~> 2.4"
    }
  }
}
