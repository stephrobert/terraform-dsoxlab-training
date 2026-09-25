# Six cas d'entrainement. Les tests en genereront d'autres, que vous ne verrez
# pas avant la correction : une resolution ecrite cas par cas ne tiendra pas.

cas = {
  duel_simple = {
    terraform_tfvars = "depuis-tfvars"
    cli_var          = "depuis-cli"
  }

  sets_normaux = {
    set_global                    = "depuis-global"
    set_org_project_scoped        = "depuis-org-projet"
    set_project_workspace_scoped  = "depuis-projet-workspace"
  }

  priorite_contre_workspace = {
    workspace        = "depuis-workspace"
    priority_global  = "depuis-priority-global"
  }

  inversion = {
    priority_project_project_scoped = "depuis-priority-projet"
    priority_org_project_scoped     = "depuis-priority-org"
  }

  fichiers = {
    terraform_tfvars = "depuis-tfvars"
    auto_tfvars      = "depuis-auto"
  }

  environnement = {
    tf_var_env = "depuis-env"
    workspace  = "depuis-workspace"
  }
}
