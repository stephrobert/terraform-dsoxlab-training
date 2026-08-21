# Projet COMPLET, applicable en l'etat. Ne rien modifier ici : le seul fichier
# a remplir est reponses.auto.tfvars.
#
# Trois familles d'instances, adressees de trois facons differentes, plus un
# module local. Les tirages sont SEEDES : ils sont donc reproductibles d'une
# machine a l'autre, mais leur resultat n'est ecrit nulle part. Pour savoir
# QUELLE instance porte l'identifiant publie, il faut interroger le state.

locals {
  services   = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta", "theta"]
  retentions = ["j1", "j7", "j30", "j90", "j365"]
}

# Ces trois tirages designent une instance de chaque famille, sans jamais dire
# laquelle : seul l'identifiant de la cible est publie en output.
resource "random_integer" "rang" {
  min  = 0
  max  = 5
  seed = "worker-v5"
}

resource "random_integer" "service" {
  min  = 0
  max  = 7
  seed = "service-v4"
}

resource "random_integer" "archive" {
  min  = 0
  max  = 4
  seed = "archive-v7"
}

# Famille 1 : indexee par POSITION (count) -> adresses random_pet.worker[N]
resource "random_pet" "worker" {
  count  = 6
  length = 2
}

# Famille 2 : indexee par CLE (for_each) -> adresses random_pet.service["cle"]
resource "random_pet" "service" {
  for_each = toset(local.services)
  length   = 2
}

resource "local_file" "journal" {
  filename = "${path.root}/journal.txt"
  content  = "workers=${length(random_pet.worker)} services=${length(random_pet.service)}\n"
}

# Une data source a la RACINE : son adresse commence bien par « data ».
data "local_file" "relecture" {
  filename   = local_file.journal.filename
  depends_on = [local_file.journal]
}

# Famille 3 : dans un MODULE -> adresses prefixees module.stockage.
# Le module existe pour une seule raison : la moitie des pieges de
# `terraform state list` n'apparaissent que sous un module.
module "stockage" {
  source     = "./modules/stockage"
  retentions = local.retentions
}
