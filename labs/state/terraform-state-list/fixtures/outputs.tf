# Les trois identifiants RECHERCHES, et le renvoi des cinq reponses.
#
# Ces outputs publient la VALEUR de l'identifiant, jamais l'adresse : c'est tout
# l'exercice. Un identifiant de random_pet ressemble a « deep-foxhound », il ne
# dit rien de l'index ni de la cle de l'instance qui le porte.

output "id_worker_recherche" {
  description = "Identifiant de l'instance de random_pet.worker a retrouver."
  value       = random_pet.worker[random_integer.rang.result].id
}

output "id_service_recherche" {
  description = "Identifiant de l'instance de random_pet.service a retrouver."
  value       = random_pet.service[local.services[random_integer.service.result]].id
}

output "id_archive_recherche" {
  description = "Identifiant de l'archive a retrouver, dans le module."
  value       = module.stockage.ids[local.retentions[random_integer.archive.result]]
}

# Renvoi des reponses de l'apprenant, pour que les tests les lisent en JSON.

output "adresse_worker" {
  value = var.adresse_worker
}

output "adresse_service" {
  value = var.adresse_service
}

output "adresse_archive" {
  value = var.adresse_archive
}

output "adresse_data_module" {
  value = var.adresse_data_module
}

output "nombre_managees" {
  value = var.nombre_managees
}
