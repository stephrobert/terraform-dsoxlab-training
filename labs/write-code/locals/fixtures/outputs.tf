# Complet, à ne pas modifier. Les sorties exposent vos locals. Notez que db_dsn
# est déjà marqué sensible : sans cela, Terraform refuserait d'exécuter une
# sortie qui dérive de var.db_password.

output "base_name" {
  value = local.base_name
}

output "node_names" {
  value = local.node_names
}

output "effective_ram" {
  value = local.effective_ram
}

output "manifest_name" {
  value = local.manifest_name
}

output "db_dsn" {
  value     = local.db_dsn
  sensitive = true
}
