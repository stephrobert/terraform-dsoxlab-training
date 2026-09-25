# DEUX FAUTES ici, d'une autre nature.
#
# Ce repertoire doit se rattacher PAR ETIQUETTES, avec un `project` declare et
# aucun `name`. Les etiquettes prennent la forme d'une MAP cle-valeur.

terraform {
  required_version = ">= 1.11.0"

  cloud {
    organization = "atelier-dsoxlab"

    workspaces {
      tags = { env = "prod" }
    }
  }

  # FAUTE 1 : un second bloc `cloud`. Il n'en existe qu'un par configuration.
  cloud {
    organization = "atelier-dsoxlab"

    # FAUTE 2 : ce bloc `workspaces` est vide, et le rattachement attendu
    # demande un `project` en plus des etiquettes.
    workspaces {
    }
  }
}
