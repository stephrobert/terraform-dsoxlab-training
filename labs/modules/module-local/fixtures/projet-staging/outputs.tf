# Sorties du projet staging. CE FICHIER EST COMPLET.

output "chemin" {
  description = "Chemin de l'artefact produit."
  value       = module.artefact.chemin
}

output "configuration" {
  description = "Ce que ce projet a demande au module."
  value       = module.artefact.configuration
}
