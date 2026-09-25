# Les quinze identifiants de source, dans le désordre

Ce sont les seuls admis. Les recopier tels quels, sans en inventer ni en
oublier.

- `set_project_workspace_scoped`
- `cli_var`
- `priority_global`
- `terraform_tfvars`
- `set_org_project_scoped`
- `priority_org_project_scoped`
- `workspace`
- `set_global`
- `priority_project_workspace_scoped`
- `auto_tfvars`
- `set_org_workspace_scoped`
- `tf_var_env`
- `priority_project_project_scoped`
- `set_project_project_scoped`
- `priority_org_workspace_scoped`

## Comment les lire

`set_<propriétaire>_<portée>_scoped` désigne un variable set **normal**, avec le
propriétaire (`org` ou `project`) puis la portée (`project` ou `workspace`).

`priority_*` désigne les mêmes, déclarés **prioritaires**.

Les quatre autres sont les sources qui ne sont pas des variable sets :
`terraform_tfvars`, `auto_tfvars`, `workspace`, `tf_var_env`, `cli_var`.

## L'inversion qui décide de tout

Chez les variable sets **normaux**, la portée la plus **étroite** gagne : un set
attaché à un workspace bat un set attaché au projet, qui bat un set global.

Chez les sets **prioritaires**, c'est l'**inverse** : le plus **large** gagne.

> When a variable set is priority, the values take precedence over any variables
> with the same key set at a more specific scope.

Presque personne ne le voit, et c'est exactement ce que le lab fait constater.
