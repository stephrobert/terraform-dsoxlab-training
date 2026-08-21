data "local_file" "publie" {
  filename = "${var.racine}/publie.json"

  # ??? Ce chemin est littéral : rien n'indiquerait sans cela qu'il faut
  #     attendre la copie faite par null_resource.publication. Posez le
  #     depends_on explicite qui manque.
  depends_on = [???]
}
