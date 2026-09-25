# Fourni. A NE PAS MODIFIER, ET C'EST IMPORTANT.
#
# La troisieme ressource ECHOUE, et c'est voulu : elle ecrit sous un chemin dont
# le parent est un fichier, ce qui ne peut pas exister. Le run se termine donc
# en erreur, apres avoir pose les deux premieres.
#
# Un run qui reussit de bout en bout n'apprendrait rien ici : tout ce qui est
# planifie aboutit, et les deux moities du flux racontent la meme chose. C'est
# quand un run echoue au milieu qu'elles divergent, et c'est cette divergence
# que le lab fait mesurer.
#
# `terraform apply` rendra donc un code non nul. C'est le resultat attendu.

terraform {
  required_version = ">= 1.11.0"

  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}

resource "local_file" "socle" {
  filename = "${path.module}/socle.txt"
  content  = "socle"
}

resource "local_file" "service" {
  filename = "${path.module}/service.txt"
  content  = "service pose sur ${local_file.socle.content}"
}

resource "local_file" "sonde" {
  # `socle.txt` est un FICHIER : rien ne peut vivre dessous.
  filename = "${path.module}/socle.txt/sonde.txt"
  content  = "sonde du ${local_file.socle.content}"
}
