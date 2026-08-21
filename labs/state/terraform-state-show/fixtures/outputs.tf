# LE SEUL FICHIER A COMPLETER. Cinq ???, cinq reponses.
#
# Appliquez d'abord (terraform init && terraform apply) : sans state, il n'y a
# rien a inspecter. Puis interrogez le state.
#
# Deux trous demandent une ADRESSE, sous la forme exacte ou le state la porte.
# Trois demandent une VALEUR : ne la recopiez pas a la main, referencez la, sans
# quoi le moindre reapply rendrait votre reponse fausse.

output "adresse_data" {
  description = "Adresse de la data source, telle qu'elle figure dans le state."
  # ??? : une chaine. Attention au prefixe des data sources.
  value = ???
}

output "adresse_replica" {
  description = "Adresse de la DEUXIEME instance de random_pet.replicas."
  # ??? : une chaine. Sans index, une adresse ne designe aucune instance et
  # `terraform state show` la refuse.
  value = ???
}

output "empreinte_inventaire" {
  description = "Empreinte SHA-256 du fichier relu par la data source."
  # ??? : une REFERENCE HCL vers l'attribut du state, pas la valeur recopiee.
  value = ???
}

output "secret_api" {
  description = "Le mot de passe genere, que state show caviarde."
  # ??? : une reference vers la valeur du mot de passe. Terraform refusera cet
  # output tant qu'il n'est pas declare sensible : c'est le point de l'exercice.
  sensitive = ???
  value     = ???
}

output "attributs_masques" {
  description = "Attributs de random_pet.env a null dans le state, donc absents de la fiche humaine."
  # ??? : la liste TRIEE de leurs noms. `state show` ne les affiche pas du tout,
  # seul `terraform show -json` les rend visibles.
  value = ???
}
