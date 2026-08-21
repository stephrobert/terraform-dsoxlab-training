# Ce fichier est COMPLET. Ne le modifiez pas.

output "parties" {
  value = [for p in data.cloudinit_config.principal.part : p.filename]
}

output "nb_parties" {
  value = length(data.cloudinit_config.principal.part)
}
