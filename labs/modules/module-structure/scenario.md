# Scenario: the standard structure of a module

**Target exam sub-objective: 4a.**

A monolithic configuration works, but the registry, documentation generators and
reviewers all expect the *Standard Module Structure*. This lab tackles the
opposite trap to the expected one: file names really are cosmetic, except
`override.tf` and `*_override.tf`, which Terraform loads last and which actually
override the configuration.

## Target capability

Refactor a monolithic configuration into a standard-format module: the
`main.tf` / `variables.tf` / `outputs.tf` / `README.md` base, an isolated
`terraform` block, a nested module under `modules/` called by relative path, a
standalone example under `examples/`, and prove from the applied state that an
`override.tf` file changes the outcome where no other file name does.

## Where the learner starts

`challenge/work` holds a single file, `tout.tf`, around sixty lines, where
everything is piled up out of order:

- the `terraform` block, with `required_version` and `required_providers` for
  `local` and `random`;
- three `variable` blocks: `nom_service`, `environnements` and
  `permissions_index`;
- two `resource` blocks: `random_pet.id`, single instead of one per environment,
  and `local_file.index` with `file_permission = "0644"`;
- one `output` block named `chemins`.

Two holes prevent parsing: the `environnements` variable carries `type = ???`,
and the `chemins` output carries `description = ???` with no `type` line at all.
No `README.md`, no `LICENSE`, no subdirectory. Nothing has been applied: no
`.terraform`, no state, no generated file.

## The state to reach

1. `tout.tf` is gone. The directory holds `main.tf`, `variables.tf`,
   `outputs.tf`, `README.md` and `LICENSE`, and the `terraform` block lives alone
   in `terraform.tf`, the name the official style guide uses (not `versions.tf`,
   which appears nowhere in HashiCorp's documentation).
2. A nested module exists under `modules/fiche/`, with its own `main.tf`,
   `variables.tf`, `outputs.tf` and a `README.md` marking it usable from outside.
   It creates one `random_pet` and one `local_file` per call.
3. The root calls that module by the relative path `./modules/fiche`, not by a
   remote address, so that Terraform treats it as part of the same package.
4. The module is instantiated once per environment: the state holds
   `module.fiche["dev"]` and `module.fiche["prod"]`, each with its two resources.
5. Every `variable` and every `output`, at the root as in the nested module,
   carries a `type` and a `description`. The root `chemins` output is a
   `map(string)` aggregating the path each module instance exposes.
6. `examples/minimal/` holds a standalone configuration calling the module, which
   `terraform validate` accepts without error.
7. An `override.tf` at the root brings `local_file.index`'s `file_permission`
   from `0644` down to `0600`. `main.tf` still declares `0644`: it is the applied
   state that must read `0600`.
8. The configuration is applied and stable: a plan replayed right after proposes
   no change.

## How it is proven

Tests run `terraform init`, `terraform apply -auto-approve`, then only query
JSON, never the learner's `.tf` files.

- `terraform show -json`: `values.root_module.child_modules[]` must hold the
  addresses `module.fiche["dev"]` and `module.fiche["prod"]`, each carrying a
  `random_pet` and a `local_file`. A missing, non-nested or non-iterated module
  fails the test. The root resource `local_file.index` must carry
  `file_permission == "0600"`: proof that `override.tf` was loaded last and won,
  impossible to obtain without that exact file name.
- `terraform plan -out` converted by `terraform show -json`:
  `configuration.root_module.module_calls.fiche.source` must be exactly
  `./modules/fiche`, and `module_calls.fiche.module.outputs` must expose the
  aggregated output. That proves the relative-path call and the nested module's
  output contract.
- `terraform output -json`: the `chemins` key must have
  `"type": ["map","string"]` and one value per environment. An output declared
  **without** a `type` comes back typed differently, and the test catches it:
  measured on 1.15.4, the same value then reads
  `["object", {"dev": "string", "prod": "string"}]`, the inferred type key by key.
- `terraform -chdir=examples/minimal init` then `validate -json`: `valid` must be
  `true` and `error_count` must be `0`.
- `terraform plan -detailed-exitcode` must exit `0`, proving a stable state.
- Finally, the presence of `README.md` at the root and in `modules/fiche/`, and of
  `LICENSE` at the root: the lab's only file check, because the official
  documentation makes it the boundary between a public and an internal
  sub-module.
