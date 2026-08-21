# Projet deja fonctionnel, a ne pas modifier. Deux ressources gerees dont le
# state doit MIGRER vers le backend configure, sans etre recree.
resource "random_pet" "app" {
  length = 2
}
resource "local_file" "marqueur" {
  filename = "${path.module}/marqueur.txt"
  content  = "app=${random_pet.app.id}\n"
}
