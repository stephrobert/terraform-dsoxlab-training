terraform {
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

# Aucune valeur par defaut : c'est VOULU. Une chaine non interactive doit
# echouer tout de suite plutot que d'attendre une saisie qui n'arrivera pas.
variable "environnement" {
  type = string
}

variable "mot_de_passe" {
  type    = string
  default = "SECRET-EN-CLAIR-12345"

  # A completer : cette variable porte un secret. Marquez-la comme telle.
  # Attention, ce marquage ne fait pas ce que la plupart des gens croient :
  # la validation ira verifier ce qu'il protege VRAIMENT.
  ???
}

resource "random_pet" "nom" {
  length = 2
}

resource "local_file" "conf" {
  filename = "${path.root}/produits/${var.environnement}.conf"
  content  = "env ${var.environnement} secret ${var.mot_de_passe}\n"
}

resource "terraform_data" "lent" {
  input = var.environnement

  provisioner "local-exec" {
    # A completer : l'apply doit durer assez longtemps pour qu'un verrou soit
    # OBSERVABLE par une commande concurrente. Au moins dix secondes.
    command = ???
  }
}
