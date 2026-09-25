# 🎯 Challenge: compose values with HCL functions

## ✅ Objective

The configuration shipped in `challenge/work` **does not validate**. Seven
`locals` and two resource attributes are replaced by `???`, and one declaration
is missing from `versions.tf`.

Complete it **with function expressions only**. No value may be hard-coded:
everything derives from the variables in `variables.tf`.

## 📋 What is supplied

| File | State |
|---|---|
| `variables.tf` | **complete, not to be modified** |
| `outputs.tf` | **complete, not to be modified** |
| `node.yaml.tftpl` | **complete, not to be modified** |
| `versions.tf` | one provider declaration is missing |
| `locals.tf` | seven `???` to replace |
| `main.tf` | two `???` to replace |

The variables are `environments_csv = "prod,dev,prod,staging"`,
`tags = { projet = "demo", equipe = "devops" }`, `environment = "qa"` and
`memory_mib = 1536`.

## 🎯 The exact values to produce

| Output | Expected value | The trap |
|---|---|---|
| `env_uniques` | `["dev", "prod", "staging"]` | the CSV holds a duplicate, and `for_each` refuses a list |
| `env_recycle` | `"staging"` | access at **index 5** over the sorted list of 3 elements |
| `taille` | `"small"` | `"qa"` is **absent** from the table, the plan must not stop |
| `tags_effectifs` | holds `projet`, `equipe`, and `env = "qa"` | the merge order decides the winner |
| `memory_gib` | `2` | 1536 MiB is 1.5 GiB, and rounding does not go down |
| `tfvars_rendu` | `env = "qa"` then `gib = 2`, one pair per line | produced by a **provider** function |

## 🧩 The three traps

1. **`element()` wraps around modulo when out of range.** Index 5 over three
   elements gives `5 % 3 = 2`. It does not fall back on the first element.
2. **`lookup()` without a fallback raises an error.** It does not return `null`.
3. **In a template, only `${` is escaped as `$${`.** The rendered files must hold
   `$HOME` and `$(date)` **intact**, as well as the literal text `${AUTRE}`.

## 🏗️ What the resource must produce

`local_file.node` creates **one file per distinct environment**, addressed in
state by the value (`["dev"]`, `["prod"]`, `["staging"]`) and not by a numeric
index. Each file receives `hostname = "node-<environment>"`.

## ⚠️ The built-in provider

The `tfvars_rendu` output requires a function from the **built-in** `terraform`
provider. Declare it in `required_providers` with the source
`terraform.io/builtin/terraform`, then **re-run `terraform init`**. Without that,
the call fails with `Unknown provider`.

## 🔍 Validation

```bash
dsoxlab check write-code-functions
```

The tests query structured state (`terraform output -json`,
`terraform show -json`), never your `.tf` files. They also check that
`terraform plan -detailed-exitcode` returns **0** after the `apply`: an unstable
expression, a timestamp for instance, would fail that check.
