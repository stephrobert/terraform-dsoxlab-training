# 🎯 Challenge: two genuinely isolated environments

## 📦 Starting point

`challenge/work` runs **offline**, `local` backend:

| Folder | What it is |
| --- | --- |
| `modules/plaque/` | the shared module, **complete** |
| `envs/dev/` | root, empty `backend "local" {}`, holed module call |
| `envs/prod/` | the same, with other values |
| `CIBLE.md` | the per-environment values and the initialisation command |

## ✅ Objective

Give each environment its own **state**, without duplicating the module or the
backend block.

## 📋 What you must obtain

1. Both roots call the shared module by a **relative** path.
2. `dev` produces **one** plate, `prod` produces **three**.
3. `etats/dev.tfstate` and `etats/prod.tfstate` exist, **outside** the roots.
4. The `backend` block stays **empty**: the path comes from `-backend-config`.
5. Both environments converge.

## ⚠️ The heart of the matter

A `backend` block accepts **no** named value:

```text
Error: Variables not allowed

Variables may not be used here.
```

Hence **partial configuration**: the block stays empty, identical everywhere, and
the missing arguments arrive at initialisation.

```bash
terraform init -backend-config=<your-file>.hcl
```

And the official argument against workspaces here is not ergonomics: "CLI
workspaces within a working directory use the **same backend**", therefore a single
set of credentials for every environment.

## 🔍 Validation

`dsoxlab check environments-separate-environments` proves, by execution:

- the backend configuration **recorded** by each root, in
  `.terraform/terraform.tfstate`;
- the resource count and outputs of each state;
- the sharing of the **same** module, read in both `modules.json`;
- **isolation**: a real `destroy` in `dev`, played on a copy, must leave `prod`'s
  state intact.

Stuck? `dsoxlab hint environments-separate-environments`.
