terraform {
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

resource "random_pet" "jeton_nord" {
  length = 2
}

resource "local_file" "plaque_nord" {
  filename = "${path.root}/plaques/nord.txt"
  content  = "plaque nord ${random_pet.jeton_nord.id}\n"
}

resource "random_pet" "jeton_sud" {
  length = 2
}

resource "local_file" "plaque_sud" {
  filename = "${path.root}/plaques/sud.txt"
  content  = "plaque sud ${random_pet.jeton_sud.id}\n"
}
