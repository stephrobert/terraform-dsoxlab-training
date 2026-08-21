# 🎯 Challenge: split without changing the plan

## 📦 Starting point

`challenge/work` runs **offline**:

| File | What it is |
| --- | --- |
| `projet/main.tf` | eighty lines carrying **everything**: `terraform` block, providers, variables, resources, outputs |
| `CIBLE.md` | the expected layout, the invariant, and the repository rules |

## ✅ Objective

Split this configuration along the **official** layout, without the plan moving by
a line, and make the repository presentable.

## 📋 What you must obtain

1. `terraform.tf`, `providers.tf`, `variables.tf`, `outputs.tf`, and a `main.tf`
   keeping only the resources.
2. `terraform.tf` carries **one** `terraform` block and **no** `provider`.
3. Variables and outputs in **alphabetical order**.
4. The plan is **identical** to the one before the split.
5. `terraform fmt -check -recursive` exits **0**.
6. A `.gitignore` ignores `.terraform/`, the state, its backups and a saved plan
   named `tfplan`, but **lets through** `.terraform.lock.hcl`.

## ⚠️ The heart of the matter

`terraform validate` proves **nothing** here: "The `validate` command does not check
if argument values are valid for a specific provider [...] It does not evaluate any
existing state." A split that loses a resource calmly prints:

```text
Success! The configuration is valid
```

So compare the **plans**, not `validate` verdicts:

```bash
terraform plan -out=apres.tfplan
terraform show -json apres.tfplan | jq -S '.planned_values, .resource_changes'
```

Two details cost dearly if missed. `terraform fmt -check` only sees the **current**
directory. And `terraform plan -out=tfplan` produces a file **without extension**,
which a `*.tfplan` pattern does not catch.

## 🔍 Validation

`dsoxlab check environments-organize-terraform-repo` proves, by execution:

- the monolithic fixture's plan is **replayed** in a temporary directory, and its
  fingerprint compared with yours;
- the layout, the single `terraform` block, the alphabetical order;
- `terraform fmt -check -recursive` from the root;
- your `.gitignore`, put to work by `git check-ignore` in a throwaway copy.

Stuck? `dsoxlab hint environments-organize-terraform-repo`.
