# Cette configuration a DEJA ECHOUE, et son state est fourni.
#
# Le `terraform.tfstate` du repertoire est celui qu'un `apply` rate a laisse :
# les deux premieres ressources sont creees, la troisieme a echoue.
#
# Regardez-le avant de toucher a quoi que ce soit :
#
#     terraform show -json | jq '.values.root_module.resources[]
#                                | {address, tainted}'
#
# La ressource fautive N'EST PAS absente du state. Elle y figure, marquee
# `tainted` : Terraform sait qu'elle est dans un etat douteux et la REMPLACERA
# au prochain apply. C'est une nuance qui compte, et qu'on lit rarement.
#
# Le reflexe de tout detruire pour repartir de zero est exactement ce que ce
# lab veut vous faire perdre : deux ressources sur trois sont parfaitement
# saines.

resource "random_pet" "identifiant" {
  length    = 2
  separator = "-"
}

resource "local_file" "inventaire" {
  filename = "${path.module}/inventaire.txt"
  content  = "identifiant : ${random_pet.identifiant.id}\n"
}

# Celle-ci echoue. Elle ecrit dans un repertoire que RIEN ne cree.
#
# Corrigez la cause dans la configuration. Ne supprimez pas la ressource, ne la
# commentez pas : la faire disparaitre n'est pas la reparer, et le lab le
# verifie.
resource "null_resource" "rapport" {
  triggers = {
    identifiant = random_pet.identifiant.id
    inventaire  = local_file.inventaire.filename
  }

  provisioner "local-exec" {
    command = "cp ${local_file.inventaire.filename} ${path.module}/sortie/rapport.txt"
  }
}
