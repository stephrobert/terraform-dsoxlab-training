# 🎯 Challenge: split a monolith without moving the plan

## Starting point

`challenge/work` holds **a single file**, `tout.tf`, piling up out of order: the
`terraform` block, three `provider` blocks, four `variable`, one `locals`, three
`resource` and three `output`.

It works perfectly. The problem is not that it is broken, it is that it is
unreadable.

There is no values file, no state, no saved plan. The `operateur` variable has
**no default**: no command will run without providing it.

## ✅ Objective

1. **Freeze the reference plan FIRST**, with `terraform plan -out` then
   `terraform show -json`, into a `plan-reference.json` file.
2. **Split** `tout.tf` into `terraform.tf`, `providers.tf`, `variables.tf`,
   `locals.tf`, `main.tf` and `outputs.tf`. **No block is added, removed or
   modified**: only their location changes. `tout.tf` must disappear.
3. **Take another plan** with the same inputs, into `plan-apres.json`.
4. **Lay down the values files**:
   - `terraform.tfvars`: `projet = "catalogue"` and `environnement = "recette"`;
   - `env.auto.tfvars`: `environnement = "production"`.
5. **Apply**, providing `operateur` through `-var`.

## 🧭 What the lab makes you observe

- **Leaving `tout.tf` in place breaks everything.** Terraform reads every `.tf`:
  your six files redeclare each block a second time.
- **The plan is strictly identical** before and after the split. File names have
  no functional effect, and that is exactly what makes the refactoring safe.
- **`env.auto.tfvars` wins over `terraform.tfvars`.** The `auto` files are
  loaded afterwards, in alphabetical order.
- **`TF_VAR_projet` does NOT win over `terraform.tfvars`.** That is the rank
  most often misplaced: an environment variable sits just above the `default`,
  and below any values file.
- **`-var` always wins**, against every other source at once.

## 🔍 Validation

```bash
dsoxlab check getting-started-terraform-project-structure
```

Thirteen tests. Plan invariance is proven by comparing both JSON documents,
address by address, after neutralising volatile fields. The split is proven
without ever running an `ls`: the test drops a probe redeclaring a block, and
`terraform validate -json` names the file of the original declaration.
Precedence is read from `terraform output -json`, never from human output.
