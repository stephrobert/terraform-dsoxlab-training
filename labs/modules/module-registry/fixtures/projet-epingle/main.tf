terraform {
  required_providers {
    local = { source = "hashicorp/local", version = ">= 2.5" }
  }
}

# Ce projet doit EPINGLER une version exacte du module de registre, la 0.24.1,
# et non la plus recente. Le module vise est `label` du namespace `cloudposse`,
# pour le provider `null` : trois parties a assembler dans le bon ordre.
module "etiquette" {
  source  = "???"
  version = "???"

  namespace = "atelier"
  name      = "nord"
}

resource "local_file" "plaque" {
  filename = "${path.root}/plaques/${module.etiquette.id}.txt"
  content  = "${module.etiquette.id}\n"
}
