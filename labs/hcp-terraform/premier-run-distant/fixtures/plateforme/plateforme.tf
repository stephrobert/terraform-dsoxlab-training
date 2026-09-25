# A COMPLETER : quatre `???`.
#
# Ce repertoire ne provisionne pas d'infrastructure : il provisionne la
# PLATEFORME qui executera votre infrastructure. Un projet, un workspace, ses
# reglages, et une variable qui vivra dans le workspace et non dans le depot.
#
# Un piege vous attend, et le provider vous previendra : l'attribut
# `execution_mode` de `tfe_workspace` est DEPRECIE. Mesure du 2026-09-25 avec le
# provider 0.81 :
#
#   Warning: Argument is deprecated
#   Use resource `tfe_workspace_settings` to modify the workspace execution
#   settings. This attribute will be removed in a future release of the provider.
#
# Un avertissement n'arrete pas un apply, et c'est bien le probleme : la
# configuration marche aujourd'hui et cassera a la prochaine version majeure du
# provider. Les reglages d'execution se posent donc dans leur propre ressource.

data "tfe_organization" "courante" {
  name = var.organisation
}

resource "tfe_project" "formation" {
  organization = data.tfe_organization.courante.name
  name         = var.projet
  description  = "Cree par le lab premier-run-distant du catalogue dsoxlab."
}

resource "tfe_workspace" "demo" {
  organization = data.tfe_organization.courante.name

  # A COMPLETER : le workspace doit naitre DANS le projet ci-dessus, et porter
  # le nom que `var.workspace` donne. Ne posez pas `execution_mode` ici.
  ???

  description = "Workspace du premier run distant. A detruire apres le lab."
}

resource "tfe_workspace_settings" "demo" {
  # A COMPLETER : c'est ici, et nulle part ailleurs, que se regle le mode
  # d'execution. Le lab veut un run qui s'execute CHEZ HCP Terraform, pas sur le
  # poste, et qui attende une confirmation humaine avant d'appliquer.
  ???
}

resource "tfe_variable" "message" {
  workspace_id = tfe_workspace.demo.id

  # A COMPLETER : une variable Terraform (et non d'environnement), nommee
  # `message`, portant `var.message`, marquee comme sensible.
  ???

  description = "Fournie par le workspace, jamais par le depot."
}

output "organisation" {
  description = "L'organisation, pour que les tests sachent ou regarder."
  value       = data.tfe_organization.courante.name
}

output "projet" {
  description = "Le projet cree."
  value       = tfe_project.formation.name
}

output "workspace" {
  description = "Le workspace cree."
  value       = tfe_workspace.demo.name
}

output "workspace_id" {
  description = "Son identifiant, celui que l'API emploie."
  value       = tfe_workspace.demo.id
}
