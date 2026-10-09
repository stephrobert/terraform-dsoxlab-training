output "machines" {
  description = "UUID de chaque machine, par rôle."
  value       = { for role, d in libvirt_domain.machine : role => d.uuid }
}
