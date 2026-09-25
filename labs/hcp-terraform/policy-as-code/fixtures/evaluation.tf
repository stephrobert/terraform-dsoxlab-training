# A COMPLETER.
#
# Une regle de conformite qui refuse un plan non conforme, et accepte le
# conforme. Les deux plans sont de VRAIES sorties de `terraform show -json`,
# capturees avec le provider `local`.
#
# La regle : aucun fichier ne doit etre cree avec des permissions accordant un
# droit au reste du monde. `0777` est refuse, `0640` passe.
#
# Les plans se lisent avec `jsondecode(file(...))`. La structure utile est
# `resource_changes[].change.after.file_permission`.

locals {
  plans = {
    conforme     = jsondecode(file("${path.module}/plans/plan-conforme.json"))
    non_conforme = jsondecode(file("${path.module}/plans/plan-non-conforme.json"))
  }

  # A COMPLETER : pour chaque plan, la liste des ADRESSES fautives.
  #
  # Une liste vide vaut conforme. Ne renvoyez pas un booleen : une regle qui
  # dit seulement « non » sans dire « ou » ne sert a personne.
  violations = {
    for nom, plan in local.plans : nom => ???
  }
}

output "violations" {
  description = "Les adresses fautives de chaque plan, vides si conforme."
  value       = local.violations
}
