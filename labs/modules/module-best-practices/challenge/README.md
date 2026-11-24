# A reusable module does not configure its providers

## The situation

**Target exam sub-objective: 5b (provider configurations in modules).**

A module carrying its own provider configuration is not merely less flexible: it
becomes **impossible to destroy cleanly**, and its call refuses `count`, `for_each`
and `depends_on`. The rest of the best practices follow the same principle:
whatever the module **decides** in place of its caller forbids reuse.

## Capability targeted

Refactor a "legacy" module into a composable one: strip its provider
configuration and have the caller pass it, turn a manufactured dependency into an
**input**, and document it, then prove each point from the artefacts Terraform
produces.

## Where the learner starts

`challenge/work` runs **offline**, with the `local` provider alone:

- `bibliotheque/plaque/main.tf`: the offending module. It declares a
  `provider "local" {}` block, and decides alone about its output directory via a
  `locals`. It has no `README.md`.
- `projet/main.tf`: a **single** call, without `for_each`, subject to the directory
  the module chose.
- `projet/outputs.tf`: supplied and correct. Its `chemins` output is a **map**
  built by a `for` over `module.plaque`: it therefore assumes a multiple call.
- `CIBLE.md`: the three practices to restore and the expected result, without
  giving the syntax.

## The state to reach

1. The module no longer declares a provider configuration.
2. The module **expects** an aliased configuration, and the project **passes** it.
3. The output directory is an **input** of the module, and the project chooses
   `sorties`.
4. The project produces **two** plates, `nord` and `sud`, from a **single** call.
5. The module carries a non-empty `README.md`.
6. The project is applied and converges.

## How it is proven

No test reads a `.tf` file. Everything is read in the plan JSON and the state JSON.

- `configuration.provider_config`: a configuration declared **inside** a module
  appears there with a **`module_address`** field. Its absence proves point 1, and
  an entry carrying an `alias` proves point 2, completed by the
  `provider_config_key` of the module's resources.
- `module_calls.plaque.module.variables` gives the module's **real interface** and
  `expressions` what the caller passes it: together they carry point 3.
- The **references** of the passed arguments (`each.key`) prove point 4 on the
  configuration side; the state JSON confirms it with two `child_modules` addressed
  `module.plaque["nord"]` and `module.plaque["sud"]`, every resource in
  `mode: managed`.
- The state's `chemins` output gives the two real paths, hence the directory
  actually retained.
- `plan -detailed-exitcode` returns 0 for point 6.

A bare `challenge/work` scores 0 out of 9. Putting the `provider` block back in the
module drops only the first test, keeping the directory in a `locals` drops only
the inversion one, and duplicating the call instead of using `for_each` drops two.

## 🎯 Challenge: make a module composable

### 📦 Starting point

`challenge/work` runs **offline**, with the `local` provider alone:

| File | What it is |
| --- | --- |
| `bibliotheque/plaque/main.tf` | the **offending** module: it configures its provider and decides its directory alone |
| `projet/main.tf` | a **single** call, subject to what the module decided |
| `projet/outputs.tf` | supplied and correct: its output is a **map**, so the call must be multiple |
| `CIBLE.md` | the three practices to restore, and what the project must obtain |

### ✅ Objective

Refactor the module until it can be **called twice** from a single block, with a
provider configuration supplied by the project and an output directory chosen by
it.

### 📋 What you must obtain

1. The module declares **no** provider configuration any more.
2. The module **declares** that it expects an aliased configuration, and the
   project **passes** it.
3. The output directory becomes an **input** of the module; the project chooses
   `sorties`.
4. The project produces **two** plates, `nord` and `sud`, from a **single** call.
5. The module carries a non-empty `README.md`.
6. The project is applied and **converges**.

### ⚠️ The heart of the matter

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

### 🔍 Validation

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
