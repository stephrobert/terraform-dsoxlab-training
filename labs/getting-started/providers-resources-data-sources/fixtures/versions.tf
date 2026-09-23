terraform {
  required_version = ">= 1.5.0"

  # A completer : les trois providers utilises par main.tf, chacun avec sa
  # `source` et une contrainte de version PESSIMISTE (`~> x.y`).
  #
  # Sans cette declaration, Terraform devine la source sur son registre par
  # defaut. La configuration s'applique quand meme, et n'est reproductible
  # nulle part.
  required_providers {
    ???
  }
}
