# 🎯 Challenge: make a module composable

## 📦 Starting point

`challenge/work` runs **offline**, with the `local` provider alone:

| File | What it is |
| --- | --- |
| `bibliotheque/plaque/main.tf` | the **offending** module: it configures its provider and decides its directory alone |
| `projet/main.tf` | a **single** call, subject to what the module decided |
| `projet/outputs.tf` | supplied and correct: its output is a **map**, so the call must be multiple |
| `CIBLE.md` | the three practices to restore, and what the project must obtain |

## ✅ Objective

Refactor the module until it can be **called twice** from a single block, with a
provider configuration supplied by the project and an output directory chosen by
it.

## 📋 What you must obtain

1. The module declares **no** provider configuration any more.
2. The module **declares** that it expects an aliased configuration, and the
   project **passes** it.
3. The output directory becomes an **input** of the module; the project chooses
   `sorties`.
4. The project produces **two** plates, `nord` and `sud`, from a **single** call.
5. The module carries a non-empty `README.md`.
6. The project is applied and **converges**.

## ⚠️ The heart of the matter

A `provider` block in a module is no style detail: "A provider configuration must
always stay present in the overall Terraform configuration for longer than all of
the resources it manages." And the call itself gets restricted:

```text
Error: Module is incompatible with count, for_each, and depends_on
```

Implicit inheritance saves nothing here: "Aliased providers are **never** inherited
automatically and must be passed explicitly using the `providers` argument." Two
declarations are therefore needed, one in the module's `required_providers`, the
other in the caller's `module` block.

## 🔍 Validation

`dsoxlab check modules-module-best-practices` proves, by execution:

- `configuration.provider_config` of the plan JSON: no entry may carry a
  **`module_address`** field, which betrays a configuration declared **inside** a
  module; one entry must carry an **`alias`**;
- `module_calls.plaque.module.variables` and `expressions`: the module's real
  interface and what the caller passes it;
- the **references** of the arguments (`each.key`), then the state JSON, with two
  `child_modules` addressed `module.plaque["nord"]` and `["sud"]`;
- the state's `chemins` output, and `plan -detailed-exitcode` at 0.

No test reads your `.tf` files.

Stuck? `dsoxlab hint modules-module-best-practices`.
