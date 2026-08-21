resource "random_pet" "temoin" {
  length = 2

  # Le temoin doit etre refait quand, et seulement quand, on change de
  # workspace.
  keepers = {
    workspace = ???
  }
}

resource "local_file" "app" {
  # `prod` produit TROIS fichiers. Tout autre environnement en produit UN.
  count = ???

  # Le nom doit porter l'environnement qui a produit le fichier, et l'index de
  # l'instance. Aucune valeur litterale `dev` ou `prod` ne doit apparaitre ici.
  filename = ???

  content = "environnement ${terraform.workspace} instance ${count.index}\n"
}
