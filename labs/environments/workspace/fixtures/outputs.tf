# Ces trois sorties sont ecrites. Ne pas les modifier : ce sont elles que la
# validation interroge, workspace par workspace.

output "workspace_actif" {
  description = "Workspace qui a produit cet etat."
  value       = terraform.workspace
}

output "fichier_produit" {
  description = "Premier fichier ecrit par ce workspace."
  value       = local_file.app[0].filename
}

output "replicas" {
  description = "Nombre d'instances produites par ce workspace."
  value       = length(local_file.app)
}
