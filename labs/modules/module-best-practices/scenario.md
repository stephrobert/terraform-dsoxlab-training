# Scenario: a reusable module does not configure its providers

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
