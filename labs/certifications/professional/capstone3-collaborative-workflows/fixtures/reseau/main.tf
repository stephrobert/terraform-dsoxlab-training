# La stack AMONT. Elle produit le socle, et le PUBLIE.
#
# A COMPLETER : le bloc `terraform` est incomplet. Il lui manque la contrainte
# sur le binaire, celle sur le provider, et le bloc qui envoie le state dans le
# bucket S3.
#
# Le bloc backend reste VIDE : ses arguments viennent de `backend.tfbackend`,
# par `terraform init -backend-config=backend.tfbackend`. Un bloc `backend`
# n'accepte aucune valeur nommee, et c'est pour cela que cette forme existe.

terraform {
  ???
}

variable "plage_reseau" {
  description = "La plage du reseau produit."
  type        = string
  default     = "10.42.0.0/16"
}

resource "random_pet" "identifiant" {
  length    = 2
  separator = "-"
}

# A COMPLETER : trois sorties, qui sont le CONTRAT de cette stack.
#
# `application/` ne peut lire que ce qui est publie ici : une valeur non exposee
# en output est invisible de l'autre cote, meme si elle est dans le state.
output "identifiant_reseau" {
  value = ???
}

output "plage_reseau" {
  value = ???
}

output "passerelle" {
  # La premiere adresse utilisable de la plage. Calculee, jamais ecrite en dur.
  value = ???
}
