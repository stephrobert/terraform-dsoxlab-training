output "id" {
  value       = module.etiquette.id
  description = "Identifiant compose par le module de registre."
}

output "plaque" {
  value       = local_file.plaque.filename
  description = "Chemin de la plaque produite."
}
