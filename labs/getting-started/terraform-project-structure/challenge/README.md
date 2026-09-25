# 🎯 Challenge: split without the plan moving

## 📦 Starting point

`challenge/work` holds **a single file**, `tout.tf`, piling up out of order the
`terraform` block, the providers, four variables, a `locals`, three resources and
four outputs.

It also holds `reference/monolithe.tf.txt`: a **reference copy**, supplied and
not modifiable, whose extension is not `.tf` so that Terraform does not load it.
The tests use it to rebuild the original plan.

## ✅ Objective

1. **Split** `tout.tf` into six files: `terraform.tf`, `providers.tf`,
   `variables.tf`, `locals.tf`, `main.tf`, `outputs.tf`. No block is added,
   removed or modified: only their location changes.
2. **Make `tout.tf` disappear.** Splitting means **moving**.
3. **Set the values**: a `terraform.tfvars` fixing `projet` and `environnement`,
   and an `env.auto.tfvars` redefining `environnement`.
4. **Apply** with `revision` supplied through `-var`, that variable being
   declared without a `default`.

The brief also fixes an environment variable, and it matters:

```bash
export TF_VAR_projet="depuis-env"
```

## 🧭 The expected values, and why

| Output | Value | Who wins |
| --- | --- | --- |
| `projet_effectif` | `depuis-tfvars` | `terraform.tfvars` beats `TF_VAR_` |
| `environnement_effectif` | `depuis-auto` | a `*.auto.tfvars` beats `terraform.tfvars` |
| `region_effective` | `eu-ouest` | nobody sets it: its `default` wins |
| `revision_effective` | `depuis-ligne-de-commande` | `-var` beats everything else |

The first line is the surprising one: `TF_VAR_` lives just above the `default`,
and **below every values file**.

## ⚠️ Copying is not splitting

If `tout.tf` stays next to the six files, every name is declared twice and
Terraform refuses: `Duplicate variable declaration`. A name is declared once per
**directory**, whichever file carries it.

## 🔍 Validation

```bash
dsoxlab check getting-started-terraform-project-structure
```

Nine tests. None opens your `.tf` files.

The central proof is **invariance**: the tests rebuild the monolith's plan from
the reference copy and compare it with yours, address by address and value by
value.

The split itself is proven by **ablation**: each file is removed in a copy, and
something must break. If removing `variables.tf` changes nothing, the variables
are not in it.

Stuck? `dsoxlab hint getting-started-terraform-project-structure`.
