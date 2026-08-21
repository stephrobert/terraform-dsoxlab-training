# 🎯 Challenge: the value that wins, and why

## 📦 Starting point

One configuration serves three environments. It is neither initialised nor
applied, and it runs **offline** (`local` and `random`).

| File | What it is |
| --- | --- |
| `versions.tf` | **complete**, leave it alone |
| `variables.tf` | `env_name` and `disk_size_gb` with **no** `default`, two types left as `???` |
| `main.tf` | `random_pet.suffixe` and `local_file.profil`, stubbed with `???` |
| `outputs.tf` | `profil` and `taille_octets`, expressions to write |
| `terraform.tfvars` | present at the root, and that is the **problem** (see below) |
| `commun.auto.tfvars` | the values shared by every environment |
| `envs/dev.tfvars` | complete |
| `envs/staging.tfvars` | one **misspelled** key |
| `envs/prod.tfvars` | **incomplete** |
| `CIBLE.md` | the precedence ladder and the expected values |

## ✅ What you must achieve

1. `terraform plan -input=false`, with **no option at all**, must **fail** on
   `No value for required variable`.
2. The missing types in `variables.tf` are declared, and the blocks in `main.tf`
   and `outputs.tf` completed.
3. `envs/staging.tfvars` no longer raises any warning.
4. `envs/prod.tfvars` is completed: **8** GB and **90** days.
5. Shared values stay in the auto-loaded file, without being copied into the
   three environment files.
6. The `prod` environment is **applied**, and a fresh plan proposes nothing.

## ⚠️ The heart of the matter

A `terraform.tfvars` is loaded **automatically**. The one sitting here supplies a
value to both variables that have no `default`: the guard rail in `variables.tf`
protects nothing any more, and `terraform plan` succeeds even though no
environment was ever chosen.

And a misspelled key in a value file does **not** fail the plan:

```text
Warning: Value for undeclared variable
```

The variable stays at its `default`, the plan is valid, and the size is wrong.

## 🔍 Validation

`dsoxlab check environments-per-environment-variables` proves, by execution:

- the value **actually retained** for each variable, read from
  `terraform show -json` (never from your files);
- that `TF_VAR_` beats the `default` but **loses** against a value file;
- that `-var` and `-var-file` are settled by **argument order**;
- that `*.auto.tfvars` files apply in **lexical** order;
- the applied state of `prod` and its idempotence.

Stuck? `dsoxlab hint environments-per-environment-variables`.
