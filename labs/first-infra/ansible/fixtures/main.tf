# Le parc simule. Chaque serveur recoit un identifiant que seul l'ordonnanceur
# connait : impossible a ecrire de tete, et c'est le but.
resource "random_id" "machine" {
  for_each    = var.parc
  byte_length = 4
}

locals {
  # A completer : les adresses.
  #
  # Elles se CALCULENT depuis `var.cidr_de_base` et l'index de chaque serveur,
  # par une fonction HCL. Une adresse recopiee a la main serait juste
  # aujourd'hui et fausse au premier changement de reseau, sans que rien ne le
  # signale.
  adresses = {
    for nom, serveur in var.parc : nom => ???
  }

  # L'inventaire, au format que Ansible attend : des groupes, et des variables
  # d'hote. Fourni, a ne pas modifier.
  inventaire = {
    for role in distinct([for s in var.parc : s.role]) : role => {
      hosts = {
        for nom, serveur in var.parc : nom => {
          ansible_host = local.adresses[nom]
          machine_id   = random_id.machine[nom].hex
        } if serveur.role == role
      }
    }
  }
}

# A completer : la ressource qui ecrit l'inventaire.
#
# Le fichier s'appelle `inventaire.json` et vit dans le repertoire du module.
# Son contenu est SERIALISE par une fonction : une concatenation de chaines
# produirait du JSON presque valide, et le presque coute une heure.
???
