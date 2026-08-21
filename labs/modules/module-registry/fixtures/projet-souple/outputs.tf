output "id" {
  value       = module.etiquette.id
  description = "Identifiant compose par l'appel a contrainte souple."
}

output "id_patch" {
  value       = module.etiquette_patch.id
  description = "Identifiant compose par l'appel a fenetre de correctifs."
}
