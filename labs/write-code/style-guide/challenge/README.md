# 🎯 Challenge: make a configuration CI-acceptable

## Starting point

`challenge/work` holds a **single-file `infra.tf`** project, plus a
`terraform.tfvars` (`replica_count = "3"`, quoted). The configuration **works**
in intent, but it is degraded on five axes and would pass no CI:

- **formatting**: 4-space indentation, unaligned `=` (`fmt -check` code 3);
- **consistency**: the content references `var.env_name`, never declared (the
  existing variable is `environment`), so `validate` fails;
- **naming**: resources in camelCase repeating their type
  (`localFileAppConfig`, `randomPetInstanceName`);
- **typing**: variables with no `type` or `description`;
- **sensitivity**: outputs with no `description`, API token not `sensitive`.

## ✅ Objective

Bring the configuration into compliance, **without changing the resources
created**:

1. `terraform fmt` passes cleanly.
2. `validate` is green: resolve the orphan reference (use `var.environment`).
3. Rename the resources to descriptive **snake_case**, without repeating the
   type.
4. **Type and describe** the four variables. `replica_count` must be `number`.
5. **Type and describe** the outputs. Mark the API token `sensitive`, and
   declare `type = number` on the replicas output.
6. Add a **`.gitignore`** that excludes `.terraform/`, `terraform.tfstate*` and
   `.tfvars`, but **not** `.terraform.lock.hcl` (mind the `.terraform*` trap).

The style guide also recommends **splitting** `infra.tf` into `terraform.tf`,
`providers.tf`, `variables.tf`, `main.tf`, `outputs.tf`: do it, it is the best
practice. The check, though, covers the invariants above.

## 🔍 Validation

```bash
dsoxlab check write-code-style-guide
```

Ten tests reading `terraform fmt -check`, `validate -json`, `show -json`,
`output -json`, return codes and the `.gitignore`: formatting, validity, the two
resources intact, snake_case names, described variables, the `number` typing, the
outputs (sensitivity, type, description), the `.gitignore`, and idempotence. None
parses your `.tf`.
