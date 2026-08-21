# Complet, ne pas modifier. Ces outputs ne referencent que des locals.
output "region"      { value = local.config.region }
output "node_count"  { value = local.config.node_count }
output "aval"        { value = local.aval }
output "zones_expr"  { value = local.zones_expr }
output "dir_present" { value = local.dir_present }
output "dir_absent"  { value = local.dir_absent }
