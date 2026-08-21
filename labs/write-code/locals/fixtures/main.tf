# Complet, à ne pas modifier. random_id.build fournit un hex inconnu au plan ;
# local_file.manifest consomme des locals que vous devez écrire dans locals.tf.

resource "random_id" "build" {
  byte_length = 8
}

resource "local_file" "manifest" {
  filename = "${path.module}/out/${local.manifest_name}"
  content = jsonencode({
    base_name     = local.base_name
    node_names    = local.node_names
    effective_ram = local.effective_ram
  })
}
