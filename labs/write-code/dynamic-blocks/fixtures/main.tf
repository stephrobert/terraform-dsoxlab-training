data "cloudinit_config" "principal" {
  gzip          = false
  base64_encode = false

  # En-tête commun à tous les hôtes. Littéral, complet : ne pas le déplacer
  # dans le bloc dynamique, il ne varie jamais.
  part {
    filename     = "00-entete"
    content_type = "text/cloud-config"
    content      = "#cloud-config\n"
  }

  # ??? Une partie par module ACTIF, triée par clé.
  #     - le filtre (actif) va dans le for_each, jamais dans le content ;
  #     - le filename est dérivé de la CLÉ du module, pas d'un rang.
  dynamic "part" {
    for_each = ???
    content {
      filename     = ???
      content_type = "text/cloud-config"
      content      = ???
    }
  }
}

resource "local_file" "rendu" {
  filename = "${path.module}/out/cloud-init.yaml"
  content  = data.cloudinit_config.principal.rendered

  # ??? IMPASSE À COMPRENDRE, pas une faute de frappe à corriger telle quelle.
  #     lifecycle est un bloc de META-ARGUMENTS : aucun dynamic ne peut le
  #     générer, Terraform les traite avant d'évaluer la moindre expression.
  #     Remplacez ce dynamic par un bloc lifecycle LITTÉRAL portant
  #     create_before_destroy = true.
  dynamic "lifecycle" {
    for_each = [1]
    content {
      create_before_destroy = true
    }
  }
}
