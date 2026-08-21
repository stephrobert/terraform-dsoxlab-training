# 🎯 Challenge: partial backend and state migration

## ✅ Objective

In `challenge/work`, switch the project from the **implicit** local backend to a
**parameterized** `local` backend, migrating the state. To do:

1. **create `backend.tf`** with a backend block in **partial configuration**:
   ```hcl
   terraform {
     backend "local" {}
   }
   ```
   (no `path` here, and definitely not `var.chemin_state`: the block refuses named
   values);
2. fill the `path` of **`dev.local.tfbackend`**:
   `path = "etat/dev/terraform.tfstate"`;
3. **create `prod.local.tfbackend`** with `path = "etat/prod/terraform.tfstate"`.

The test first applies with no backend, then migrates with
`terraform init -migrate-state -backend-config=dev.local.tfbackend`.

## 🔍 Validation

`dsoxlab check state-backends` proves, on JSON:

- the **`lineage`** is the same before and after: the state **migrated**, was not
  recreated; two `mode: managed` resources;
- `.terraform/terraform.tfstate` carries `backend.type = local` and
  `backend.config.path = etat/dev/terraform.tfstate`;
- the config is **partial**: in a copy, `init` without `-backend-config` resolves
  `path` to `null`, and `-backend-config=prod...` resolves to `etat/prod`;
- idempotence (`plan -detailed-exitcode` = 0).

Stuck? `dsoxlab hint state-backends`.
