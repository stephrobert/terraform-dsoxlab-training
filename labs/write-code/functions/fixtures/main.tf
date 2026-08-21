# Un fichier rendu par environnement DISTINCT.

resource "local_file" "node" {
  # ??? La source doit produire des cles d'instance ("dev", "prod", "staging"),
  #     pas des index numeriques.
  for_each = ???

  filename = "${path.module}/rendu-${each.value}.yaml"

  # ??? Rendre node.yaml.tftpl en lui passant hostname = "node-<environnement>".
  content = ???
}
