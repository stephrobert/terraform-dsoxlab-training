# Quatre ressources. Trois forment une chaine de dependances explicite, la
# quatrieme est independante et sert de temoin.

resource "random_pet" "suffixe" {
  length    = 2
  separator = "-"
}

resource "local_file" "inventaire" {
  filename = "${path.module}/inventaire-${random_pet.suffixe.id}.txt"
  content  = "suffixe : ${random_pet.suffixe.id}\n"

  # A completer : la protection.
  #
  # Ce fichier ne doit pas pouvoir etre detruit par megarde. Le meta-argument
  # qui l'interdit fait ECHOUER tout `destroy` qui l'emporterait, y compris un
  # `destroy` global lance sans y penser.
  #
  # Attention : il ne protege pas de tout, et le lab vous le fera constater.
  lifecycle {
    ???
  }
}

resource "null_resource" "empreinte" {
  triggers = {
    inventaire = local_file.inventaire.filename
  }
}

# Le temoin. Il ne depend de rien et rien ne depend de lui : c'est ce qui
# permet de le retirer du code sans toucher au reste.
resource "random_pet" "temoin" {
  length    = 3
  separator = "-"
}
