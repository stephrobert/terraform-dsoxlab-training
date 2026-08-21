resource "random_pet" "suffixe" {
  length = 2

  # Le suffixe doit etre refait quand, et seulement quand, on change
  # d'environnement.
  keepers = {
    environnement = ???
  }
}

resource "local_file" "profil" {
  filename = "${path.root}/profils/${var.env_name}.json"

  # Le profil consigne les valeurs REELLEMENT retenues, ce qui en fait la
  # trace de la precedence pour l'environnement courant.
  #
  # Le saut de ligne final n'est pas cosmetique : l'id d'un local_file est
  # l'empreinte de son CONTENU, et un fichier texte sans newline final voit
  # son empreinte changer des qu'un outil en ajoute un.
  content = format("%s\n", jsonencode({
    environnement = ???
    disque_go     = ???
    retention     = ???
    image         = ???
    tags          = ???
    suffixe       = ???
  }))
}
