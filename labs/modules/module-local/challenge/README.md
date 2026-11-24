# Wire several projects onto one shared local module

## The situation

**Target exam sub-objective: 4b (use a module).**

Terraform only treats a path as local when it begins with `./` or `../`:
everything else, absolute paths included, becomes a package copied into the module
cache. This lab makes the difference visible in
`.terraform/modules/modules.json`.

## Capability targeted

Wire several independent root configurations onto one shared local module, then
prove, from Terraform's generated artefacts alone, which folder each call really
reads and which arguments the caller really passed.

## Where the learner starts

`challenge/work` holds five folders, no `.terraform/`, no state.

- `modules-partages/artefact/` and `modules-partages/nom/`: two complete modules,
  not to be modified. `artefact` declares the `local` and `random` providers, the
  variables `nom` (required) and `suffixe_aleatoire` (boolean, default `true`), a
  `local_file`, the outputs `chemin` and `configuration`, and calls `nom` through
  `source = "../nom"`.
- `projet-dev/`: `module "artefact"` with `source = "???"`, a parasitic
  `version = "~> 1.0"` argument, `nom` already filled in, correct `outputs.tf`.
- `projet-staging/`: `module "artefact"` entirely holed, `source` and arguments as
  `???`, `outputs.tf` supplied.
- `projet-fige/`: `module "nom"` whose `source` alone is holed, with the
  instruction to demonstrate the absolute-path case there. It targets
  `modules-partages/nom` and not `artefact`, for a measured reason: an absolute
  path turns the module into a **package**, and the internal `source = "../nom"`
  of `artefact` then escapes that package. The `init` fails on `Local module path
  escapes module package`, which would prevent any observation.

## The state to reach

1. `projet-dev` is initialised and applied: its `modules.json` holds the entry
   `Key: "artefact"`, `Source` starting with `../`, `Dir` outside `.terraform/`.
2. The same file holds the chained entry `Key: "artefact.nom"`, `Source` being
   `../nom` and `Dir` normalised to `modules-partages/nom`.
3. The `projet-dev` module call no longer carries any `version` argument.
4. `projet-dev` does not pass `suffixe_aleatoire`, and the module output is still
   `true`: the module's default value applies.
5. `projet-staging` is applied from the same module, with a different `nom` and
   `suffixe_aleatoire` at `false`, in a separate state at the identical address.
6. `projet-fige` is initialised, never applied, with an absolute `source`: its
   `modules.json` then holds a `Source` in `file://` and a `Dir` under
   `.terraform/`. Verified on 1.15.4: that `Dir` is a **symbolic link** to the
   source, not the deep copy the documentation's word "copy" suggests.
7. `projet-dev` and `projet-staging` are converged, no change pending.

## How it is proven

No test reads a learner `.tf` file, and none parses human-readable output.

- The three `modules.json`, written by Terraform, loaded as JSON and indexed by
  `Key`: points 1, 2 and 6 are read in the `Source` and `Dir` pairs.
- `plan -out` then `show -json` of the plan:
  `configuration.root_module.module_calls.artefact` gives the retained `source`,
  the absence of a `version` key (point 3) and the supplied `expressions`, whose
  missing `suffixe_aleatoire` on the dev side proves point 4.
- `show -json` of the state: `values.root_module.child_modules[]` exposes
  `address == "module.artefact"` in `mode: managed`, with different values in two
  separate states (point 5), and `output -json` confirms `true` then `false`.
- `plan -detailed-exitcode` returns 0 on dev and staging (point 7). A last test
  modifies the shared module, replays that plan without `init`, requires exit code
  2, then restores and requires 0 again: a relative local module is never cached.

## 🎯 Challenge: three projects, one shared module

### 📦 Starting point

`challenge/work` holds five folders and no state:

| Folder | What it is |
| --- | --- |
| `modules-partages/artefact/` | complete module, **do not modify**. It calls `../nom` itself |
| `modules-partages/nom/` | complete module, **do not modify** |
| `projet-dev/` | holed `source`, **and one argument too many** |
| `projet-staging/` | `source` and arguments entirely holed |
| `projet-fige/` | holed `source`, to fill with an **absolute path** |

Each project is an **independent root**: its own `init`, its own state, its own
reading of the shared module.

### ✅ Objective

Wire these three projects onto the shared module, then prove **from Terraform's
own artefacts** which folder each call really reads.

### 📋 What you must obtain

1. `projet-dev` initialised and applied: its `modules.json` holds the `artefact`
   entry with a `Source` starting with `../` and a `Dir` **outside**
   `.terraform/`.
2. The same file holds the chained entry `artefact.nom`, `Source` being `../nom`
   and `Dir` normalised to `modules-partages/nom`.
3. The `projet-dev` call carries **no** `version` argument any more.
4. `projet-dev` does **not** pass `suffixe_aleatoire`, and the output is still
   `true`: the module default applies.
5. `projet-staging` applied from the **same** module, with a different `nom` and
   `suffixe_aleatoire = false`.
6. `projet-fige` **initialised, never applied**, with an **absolute** `source`:
   its `modules.json` then holds a `Source` in `file://` and a `Dir` **under**
   `.terraform/`.
7. `projet-dev` and `projet-staging` converge: no change pending.

### ⚠️ The heart of the matter

Terraform does not guess that a path is local, it **recognises it by its
prefix**: "A local path **must** begin with either `./` or `../`". Everything
else heads for another mechanism.

| What you write | What Terraform does with it |
| --- | --- |
| `../modules-partages/artefact` | **read in place**, `Dir` outside the cache |
| `modules-partages/artefact` | refused: `Invalid module source address` |
| an **absolute** path | **remote package**: `Downloading file://...`, `Dir` under `.terraform/` |

Two consequences for `projet-fige`. It targets `modules-partages/nom` and not
`artefact`, because a module turned into a package can no longer reach anything
**above it**: the internal `../nom` of `artefact` would fail the init on `Local
module path escapes module package`. And the `version` argument in `projet-dev`
only makes sense for a **registry** module: on a local source, the init stops on
`Invalid registry module source address`.

### 🔍 Validation

`dsoxlab check modules-module-local` proves, by execution:

- the three `modules.json`, written by Terraform, are read as JSON and indexed by
  `Key`: the `Source` and `Dir` pairs carry points 1, 2 and 6;
- `projet-dev`'s `.terraform/modules/` holds **only** `modules.json`, no copied
  folder;
- the plan JSON shows the absence of `version` and of `suffixe_aleatoire` in the
  dev call;
- both applied projects expose **different** configurations from the **same**
  module;
- one test modifies the shared module in a **copy**, replans **without `init`**,
  and requires exit code **2**: a relative local module is never cached;
- `plan -detailed-exitcode` returns **0** on dev and staging.

No test reads your `.tf` files.

Stuck? `dsoxlab hint modules-module-local`.
