# Configuration par defaut du provider random (ne pas modifier).
provider "random" {}

# ??? : une SECONDE configuration du MEME provider random, distinguee par un
# alias nomme "secondaire". Sans alias, ce serait un doublon refuse
# (Duplicate provider configuration). Remplacez ce ??? par l'argument.
provider "random" {
  ???
}

# Ressource sur la configuration PAR DEFAUT (ne pas modifier).
resource "random_pet" "defaut" {
  length = 2
}

resource "random_pet" "autre" {
  # ??? : rattacher cette ressource a la configuration ALIASEE "secondaire".
  # Remplacez ce ??? par le meta-argument adapte.
  ???

  length = 2
}
