terraform {
  required_version = ">= 1.11.0"

  required_providers {
    random = {
      source  = "hashicorp/random"
      version = ">= 3.6"
    }
  }

  # ─────────────────────────────────────────────────────────────────────────
  # CE BLOC EST PIEGE, DEUX FOIS.
  #
  # 1. Il reference une valeur nommee. Lancez `terraform init` et lisez la
  #    reponse : elle est sans appel, et elle explique pourquoi la
  #    configuration PARTIELLE existe.
  # 2. Il ne demande aucun verrouillage. Or le verrou du backend S3 est un
  #    OPT-IN : sans l'argument qui va bien, un fichier de verrou depose dans
  #    le bucket est purement ignore, et deux applies concurrents s'ecrasent.
  #
  # Le fichier floci.s3.tfbackend, a cote, attend d'etre complete.
  # ─────────────────────────────────────────────────────────────────────────
  backend "s3" {
    bucket = var.backend_bucket
  }
}

variable "backend_bucket" {
  description = "Nom du bucket de state. Ne peut PAS servir dans le bloc backend."
  type        = string
  default     = "tf-state-lab"
}

variable "graine" {
  description = "Change cette valeur pour verifier que l'aval suit."
  type        = string
  default     = "un"
}

resource "random_pet" "reseau" {
  length = 2

  keepers = {
    graine = var.graine
  }
}

# Les trois sorties publiees par cette stack. Ce sont elles, et elles seules,
# qu'une autre configuration pourra lire.

output "network_name" {
  description = "Nom du reseau produit."
  value       = random_pet.reseau.id
}

output "network_cidr" {
  description = "Plage reseau servie."
  value       = "10.42.0.0/16"
}

output "region" {
  description = "Region servie."
  value       = "eu-west-3"
}
