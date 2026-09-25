# Fourni. A NE PAS MODIFIER.
#
# Ce que ce run cree est volontairement sans consequence : un nom tire au sort.
# Ce qui compte n'est pas la ressource, c'est OU elle est calculee. Le plan et
# l'apply tourneront sur une machine jetable de HCP Terraform, et le state y
# restera.
#
# La variable `message`, elle, n'est declaree nulle part dans ce repertoire avec
# une valeur : c'est le WORKSPACE qui la fournit au run. Si vous lancez ce
# repertoire sans rattachement, Terraform vous la demandera ; rattache, il ne
# vous demandera rien, et c'est toute la demonstration.

variable "message" {
  description = "Fournie par le workspace, jamais par ce depot."
  type        = string
  sensitive   = true
}

resource "random_pet" "preuve" {
  length = 3

  keepers = {
    # Le run se rejoue a l'identique tant que le message ne change pas.
    message = sha256(var.message)
  }
}

output "preuve_du_run" {
  description = "Le nom tire au sort par le run distant."
  value       = random_pet.preuve.id
}

output "empreinte_du_message" {
  description = <<-TXT
    L'empreinte de la variable du workspace, et non sa valeur.

    Mesure du 2026-09-25 : Terraform propage la sensibilite A TRAVERS les
    fonctions, sans regarder ce qu'elles font. `sha256(var.message)` est donc
    tenu pour sensible, bien qu'une empreinte ne permette pas de remonter au
    secret, et un output racine qui en derive doit etre annote. Sans cela :

        Error: Output refers to sensitive values
  TXT

  value     = sha256(var.message)
  sensitive = true
}
