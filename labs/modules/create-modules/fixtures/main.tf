# L'appel du module, A COMPLETER.
#
# Un SEUL bloc `module` produit les trois environnements, grace a `for_each`.
# C'est la forme recommandee par la documentation : « You can configure Terraform
# to provision multiple instances of the same module resources in one module
# block, instead of adding multiple blocks to your configuration ».
#
# Lancez `terraform init` avant toute modification : le message d'erreur nomme
# le probleme ET la solution.

module "livrable" {
  source   = "./modules/livrable"
  for_each = var.environnements

  # ??? : le module attend une configuration de provider ALIASEE que l'heritage
  # ne peut pas lui donner tout seul. C'est ici qu'elle se passe, par un
  # argument dont le nom est celui d'un bloc que vous n'avez pas encore ecrit.
  #
  # providers = {
  #   ??? = ???
  # }

  nom       = each.key
  cible     = each.value.cible
  retention = each.value.retention
}
