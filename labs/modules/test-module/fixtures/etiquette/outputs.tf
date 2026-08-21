output "etiquette" {
  value       = local.etiquette
  description = "Etiquette composee par le module."
}

output "longueur" {
  value       = length(local.etiquette)
  description = "Nombre de caracteres de l'etiquette."
}
