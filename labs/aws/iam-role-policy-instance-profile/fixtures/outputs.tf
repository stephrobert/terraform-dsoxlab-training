# Les tests lisent ces sorties : elles sont le seul moyen de leur montrer le
# JSON produit sans relire vos `.tf`.

output "trust_policy_json" {
  description = "Le document de confiance, tel que la data source l'a fabrique."
  value       = ???
}

output "permissions_json" {
  description = "Le document de permissions."
  value       = ???
}

output "role_name" {
  value = ???
}

output "policy_arn" {
  value = ???
}

output "instance_profile_name" {
  value = ???
}
