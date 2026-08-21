terraform {
  # ??? : quelle version minimale de Terraform introduit la syntaxe
  #       provider::<nom>::<fonction> ?
  required_version = ???

  required_providers {
    # A COMPLETER : declarez ici, EN PLUS de local, le provider INTEGRE
    # `terraform` sous le nom local `tfcore` (source
    # terraform.io/builtin/terraform). Ses fonctions s'appelleront alors
    # provider::tfcore::<fonction>. Sans cette declaration, l'appel echoue
    # avec « Unknown provider function ».
    local = {
      source = "hashicorp/local"
      # ??? : la contrainte qui admet la version exposant la fonction direxists.
      version = ???
    }
  }
}
