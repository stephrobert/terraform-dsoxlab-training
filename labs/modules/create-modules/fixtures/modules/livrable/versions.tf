# Exigences du MODULE ENFANT.
#
# Un module declare toujours ses propres `required_providers` : les
# CONFIGURATIONS de provider sont heritees de l'appelant, jamais les exigences
# de source et de version.
#
# ??? : ce module utilise une seconde configuration de `local`, aliasee, pour
# ecrire les archives. Une configuration aliasee ne s'herite pas toute seule :
# le module doit DECLARER qu'il l'attend, sur une ligne a ajouter ci-dessous.

terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = ">= 2.5"
    }
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6"
    }
    tls = {
      source  = "hashicorp/tls"
      version = ">= 4.0"
    }
  }
}
