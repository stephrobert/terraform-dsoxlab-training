# Lot d'artefacts locaux en fin de vie, applique par l'equipe precedente.
#
# Ce fichier est a MODIFIER : retirer un bloc `resource`, et retirer une cle
# d'un `for_each`, font partie de l'exercice.
#
# Un premier `terraform init` puis `terraform apply` pose l'etat de depart :
# huit adresses au state, sept fichiers sur le disque.

terraform {
  required_version = ">= 1.7"
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

# La source de noms du lot. Elle reste geree du debut a la fin : son
# identifiant, ecrit dans chaque fichier, prouve qu'aucun fichier legue n'a
# ete recree en cours de route.
resource "random_pet" "jeton" {
  length = 2
}

# Les rapports sont LEGUES a l'equipe metier : ils sortent du state, leurs
# fichiers restent sur le disque.
resource "local_file" "rapports" {
  for_each = toset(["mensuel", "annuel"])
  filename = "${path.root}/rapport-${each.key}.txt"
  content  = "rapport ${each.key} - ${random_pet.jeton.id}\n"
}

# Trois bacs, dont UN SEUL doit sortir du state. Les deux autres restent
# geres, avec leurs fichiers intacts.
resource "local_file" "bacs" {
  for_each = toset(["alpha", "beta", "gamma"])
  filename = "${path.root}/bac-${each.key}.txt"
  content  = "bac ${each.key} - ${random_pet.jeton.id}\n"
}

# Le cache, lui, doit DISPARAITRE : state et fichier.
resource "local_file" "cache" {
  filename = "${path.root}/cache.txt"
  content  = "cache - ${random_pet.jeton.id}\n"
}

# Les journaux changent de main au prochain cycle : la migration se PREPARE,
# elle ne s'applique pas.
resource "local_file" "journaux" {
  filename = "${path.root}/journaux.txt"
  content  = "journaux - ${random_pet.jeton.id}\n"
}
