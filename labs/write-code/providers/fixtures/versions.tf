terraform {
  required_version = ">= 1.15.0"

  required_providers {
    random = {
      # ??? : l'adresse SOURCE complete du provider random. Ecrivez-la
      # explicitement (namespace/type), meme pour un provider HashiCorp :
      # l'omission du prefixe hashicorp/ n'est qu'une retro-compatibilite.
      source  = ???
      version = "~> 3.6"
    }
  }
}
