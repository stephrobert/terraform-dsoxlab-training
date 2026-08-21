terraform {
  # ??? : contraindre Terraform a AU MOINS 1.15.0. La contrainte du bloc
  # terraform est forcement un LITTERAL (aucune variable, aucun local n'y est
  # accepte : « Variables not allowed »).
  required_version = ???

  required_providers {
    local = {
      source = "hashicorp/local"
      # ??? : EPINGLER exactement la version 2.5.1 du provider local. Quel
      # operateur fixe une version unique ?
      version = ???
    }
    random = {
      source = "hashicorp/random"
      # ??? : autoriser toute la serie 3.x compatible (a partir de 3.6), mais
      # JAMAIS la 4.0. L'operateur pessimiste est fait pour ca.
      version = ???
    }
  }
}
