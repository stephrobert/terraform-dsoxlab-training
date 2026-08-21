# Deux ressources triviales, juste pour tirer les deux providers (ne pas modifier).
resource "random_pet" "p" {
  length = 2
}

resource "local_file" "f" {
  filename = "${path.module}/out/marqueur.txt"
  content  = "x"
}
