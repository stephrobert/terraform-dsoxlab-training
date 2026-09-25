# A COMPLETER : cinq affirmations a trancher, en booleen.
#
# Elles se lisent dans la documentation de HCP Terraform, elles ne se devinent
# pas.

locals {
  reponses = {
    # Un variable set applique a un workspace prend effet au prochain run, sans
    # qu'il faille rejouer quoi que ce soit a la main.
    set_prend_effet_au_prochain_run = ???

    # En mode d'execution `local`, HCP Terraform applique quand meme les
    # variables du workspace a l'execution.
    mode_local_applique_les_variables = ???

    # Une variable HCL de HCP Terraform doit porter une valeur ecrite en syntaxe
    # HCL, et non une chaine brute.
    variable_hcl_attend_de_la_syntaxe = ???

    # Une variable marquee sensible peut etre relue depuis l'interface apres
    # avoir ete enregistree.
    variable_sensible_relisible = ???

    # Un fichier `*.auto.tfvars` l'emporte sur `terraform.tfvars`.
    auto_tfvars_bat_terraform_tfvars = ???
  }
}

output "reponses" {
  description = "Les cinq affirmations, tranchees."
  value       = local.reponses
}
