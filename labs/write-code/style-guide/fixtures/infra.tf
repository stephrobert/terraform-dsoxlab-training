# Configuration volontairement DEGRADEE sur cinq axes : formatage (indentation
# a 4 espaces, = non alignes), coherence (reference orpheline var.env_name),
# nommage (ressources en camelCase repetant leur type), typage (variables sans
# type ni description), sensibilite/documentation (outputs sans description, le
# jeton d'API non marque sensible). A vous de la rendre conforme.

terraform {
    required_version = ">= 1.15.0"
    required_providers {
        local = { source = "hashicorp/local", version = "~> 2.5" }
        random = { source = "hashicorp/random", version = "~> 3.6" }
    }
}

variable "app_name" {
    default = "boutique"
}

variable "environment" {
    default = "dev"
}

variable "replica_count" {
    default = 2
}

variable "api_token" {
    default = "tok-demo"
}

resource "random_pet" "randomPetInstanceName" {
    length = 2
}

resource "local_file" "localFileAppConfig" {
    filename = "${path.module}/out/${random_pet.randomPetInstanceName.id}.conf"
    content = "app=${var.app_name}\nenv=${var.env_name}\nreplicas=${var.replica_count}\n"
}

output "config_path" {
    value = local_file.localFileAppConfig.filename
}

output "replicas" {
    value = var.replica_count
}

output "api_token" {
    value = var.api_token
}
