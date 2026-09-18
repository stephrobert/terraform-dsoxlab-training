# FOURNI, complet, a ne pas modifier.
#
# Cette configuration ne s'applique pas telle quelle, et c'est voulu : la
# premiere ressource designe son provider par un ALIAS. Tant que ce provider
# n'est pas configure, Terraform repond « Provider configuration not present ».
#
# C'est le point du lab. Un provider ne se devine pas : il se NOMME, avec sa
# source et sa contrainte de version. Sans cette declaration, chaque binaire
# resout ce qu'il veut, sur le registre qu'il veut.

resource "random_pet" "nom" {
  provider  = random.principal
  length    = 2
  separator = "-"
}

resource "local_file" "rapport" {
  content  = "identifiant : ${random_pet.nom.id}\n"
  filename = "${path.module}/rapport.txt"
}

resource "null_resource" "empreinte" {
  triggers = {
    identifiant = random_pet.nom.id
  }
}

output "nom_animal" {
  value = random_pet.nom.id
}
