output "noms_workers" {
  # La liste des id des workers. Un `count` s'expose bien par une expression
  # splat `ressource[*].attribut`.
  value = ???
}

output "chemins_services" {
  # Une map { cle => chemin } des services. Attention : le splat ne s'applique
  # PAS a une ressource `for_each` (elle est deja une map) : utilisez une
  # expression `for`.
  value = ???
}

output "rapport" {
  # `rapport` a 0 ou 1 instance : rendez le chemin unique, ou null s'il est
  # absent. Une fonction dediee reduit une liste de 0 ou 1 element.
  value = ???
}
