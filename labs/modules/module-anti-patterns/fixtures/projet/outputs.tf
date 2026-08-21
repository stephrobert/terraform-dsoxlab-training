output "chemins" {
  value = {
    nord = local_file.plaque_nord.filename
    sud  = local_file.plaque_sud.filename
  }
}

output "jetons" {
  value = {
    nord = random_pet.jeton_nord.id
    sud  = random_pet.jeton_sud.id
  }
}
