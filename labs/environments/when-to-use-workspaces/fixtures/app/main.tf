# La configuration racine de l'APPLICATION : deployee souvent, et par une autre
# equipe que le socle.
#
# Elle a besoin d'une valeur produite par `socle/`. Aucune expression ne
# traverse la frontiere entre deux racines : la seule passerelle est la lecture
# de l'ETAT distant de l'autre configuration, par ses outputs declares.

terraform {
  required_providers {
    local = { source = "hashicorp/local", version = ">= 2.5" }
  }
}

# A completer : lire l'etat du socle. Le backend est `local`, et son etat vit
# dans le repertoire voisin.
data "???" "???" {
  backend = ???

  config = {
    ???
  }
}

resource "local_file" "app" {
  filename = "${path.root}/produits/app.conf"

  # A completer : la valeur doit VENIR du socle, jamais etre recopiee ici.
  content = "app branchee sur le reseau ${???}\n"
}

output "reseau_consomme" {
  description = "Identifiant du reseau, lu dans l'etat du socle."
  value       = ???
}
