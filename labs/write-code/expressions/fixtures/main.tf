resource "random_pet" "hote" {
  length = 2
}

resource "local_file" "marqueur" {
  # La reference a une ressource geree s'ecrit SANS prefixe : random_pet.hote.id.
  filename = "${path.module}/out/marqueur-${random_pet.hote.id}.txt"
  content  = "hote=${random_pet.hote.id}\n"

  # ??? : rendre la permission optionnelle. Quand var.perm_forcee vaut "" (le
  # defaut), l'argument doit etre OMIS, ce qui en Terraform s'exprime par la
  # valeur null, PAS par la chaine vide (qui serait une permission invalide).
  file_permission = ???
}
