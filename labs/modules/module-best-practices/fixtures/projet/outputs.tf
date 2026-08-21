output "chemins" {
  value       = { for cle, appel in module.plaque : cle => appel.chemin }
  description = "Chemin de chaque plaque produite, par etiquette."
}
