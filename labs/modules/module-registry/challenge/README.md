# Consume a registry module and control the installed version

## The situation

**Target exam sub-objective: 4b (use a module).**

Wiring a public module is trivial; knowing which version actually runs is not: the
lock file covers **only** providers, and "Terraform does not remember version
selections for remote modules".

## Capability targeted

Derive a module's registry address from its repository name, call it with three
different constraints and obtain three distinct resolutions, address a
sub-directory of a Git repository, then prove from Terraform's artefacts alone
which version got **installed** and which constraint was **written**.

## Where the learner starts

**Network prerequisite**: the `terraform init` runs must reach
`registry.terraform.io` and `github.com`. The chosen module,
`cloudposse/label/null`, declares no provider and applies without a cloud
account: it produces only locals and outputs.

`challenge/work` holds three independent projects, no state.

- `projet-epingle/`: a `module "etiquette"` whose `source` and `version` are
  `"???"`, plus an already-written `local_file` consuming the module output, and a
  correct `outputs.tf`. It is the only project declaring a provider.
- `projet-souple/`: **two** calls of the same module, `etiquette` and
  `etiquette_patch`, both holed. The first must accept the whole `0.x` series, the
  second stay within the patches of `0.24.1`.
- `projet-sous-module/`: a `module "exports"` whose `source` must target the
  `exports` sub-directory of the `cloudposse/terraform-null-label` repository,
  pinned on tag `0.25.0`. That project only initialises, it is never applied.

Each fixture's comment states the requirement without giving the address: the
repository plus the `terraform-<PROVIDER>-<NAME>` convention are enough to
reconstruct `cloudposse/label/null`.

## The state to reach

1. `projet-epingle` installs **exactly** `0.24.1`, and its `modules.json` carries
   the `Version` key that no local module ever has.
2. The constraint written in that project is an **exact** version, readable in the
   plan JSON under `module_calls.etiquette.version_constraint`.
3. That project's `.terraform.lock.hcl` mentions the `hashicorp/local` provider
   and **no** trace of the module.
4. `projet-souple` produces **no** lock file at all: its only dependency is a
   registry module.
5. Its `etiquette` call carries a **flexible** constraint and resolves `0.25.0`,
   the newest that satisfies it, while staying below `1.0.0`.
6. Its `etiquette_patch` call resolves `0.24.1`: two versions of the **same**
   module coexist in a single `modules.json`, resolution happening per **call**.
7. `projet-sous-module` is initialised with a `source` whose `//exports` precedes
   `?ref=0.25.0`, its `Dir` pointing at the sub-directory, and its `modules.json`
   carrying the chained `exports.this` entry.
8. Both applied projects expose `atelier-nord`, `atelier-sud` and
   `atelier-sud-patch`, and propose no further change.

## How it is proven

No test reads a learner `.tf` file, and none parses human-readable output.

- The three `.terraform/modules/modules.json`, written by Terraform at install
  time, loaded as JSON and indexed by `Key`: the `Source`, `Version` and `Dir`
  fields carry points 1, 5, 6 and 7. That is the only possible proof of the
  resolved version, since this module declares no resource, so
  `terraform show -json` exposes no `child_modules`.
- `plan -out` then `show -json` of the plan: `version_constraint` gives the
  **written** constraint, distinct from the resolved version (points 2, 5 and 6).
- The `.terraform.lock.hcl`, also produced by the tool: present with the single
  provider in one case (point 3), **absent** in the other (point 4).
- `output -json` for the three labels, and `plan -detailed-exitcode` at 0 for
  convergence (point 8).

A bare `challenge/work` fails everywhere (the `init` stops on `Invalid version
constraint`), copying the same constraint into both `projet-souple` calls fails on
point 6 alone, and swapping `//` and `?ref=` makes the `init` fail on
`invalid ref: "0.25.0//exports"`.

## 🎯 Challenge: three projects, one public module, three resolutions

### 🌐 Prerequisite

This lab needs **network access**: the `terraform init` runs reach
`registry.terraform.io` and `github.com`. No cloud account is required, the target
module declares no provider.

### 📦 Starting point

`challenge/work` holds three independent projects and no state:

| Folder | What you must write there |
| --- | --- |
| `projet-epingle/` | `source` and `version` of one call, as an **exact** version |
| `projet-souple/` | **two** calls of the same module, two different constraints |
| `projet-sous-module/` | a **Git** `source` targeting a sub-directory, on a tag |

The target module is published by the **`cloudposse`** organisation, in the
**`terraform-null-label`** repository. Its registry address is not invented, it is
**derived**: the publishing convention imposes a repository name of the form
`terraform-<PROVIDER>-<NAME>`, and the address is written
`<NAMESPACE>/<NAME>/<PROVIDER>`.

### ✅ Objective

Obtain **three different resolutions** of the same module, then prove from
Terraform's artefacts which one got installed where.

### 📋 What you must obtain

1. `projet-epingle` installs **exactly** `0.24.1`, with an **exact** version
   constraint.
2. That project's `.terraform.lock.hcl` mentions **only** the `hashicorp/local`
   provider, never the module.
3. `projet-souple` produces **no** `.terraform.lock.hcl` at all.
4. Its `etiquette` call accepts the whole `0.x` series **without** allowing a
   `1.x`, and therefore resolves `0.25.0`.
5. Its `etiquette_patch` call stays within the **patches** of `0.24.1`, and
   therefore resolves `0.24.1` while `0.25.0` is available.
6. `projet-sous-module` is **initialised** (never applied) with a Git address
   targeting the `exports` sub-directory, on tag `0.25.0`.
7. Both applied projects expose `atelier-nord`, `atelier-sud` and
   `atelier-sud-patch`, and converge.

### ⚠️ The heart of the matter

The lock file **locks no module**: "the dependency lock file tracks only
**provider** dependencies". The only thing that pins a module version is the
**constraint** you write.

| What you write | What Terraform installs |
| --- | --- |
| nothing at all | the **newest** available |
| `"0.24.1"` | exactly that one |
| `"~> 0.24"` | the newest of the `0.x` |
| `"~> 0.24.1"` | the newest of the `0.24.x` |

And order matters in a Git address: "the sub-directory portion must be **before**
those arguments". The sub-directory therefore comes **before** the `?ref=`,
otherwise the revision becomes `0.25.0//exports`, which does not exist.

### 🔍 Validation

`dsoxlab check modules-module-registry` proves, by execution:

- the three `.terraform/modules/modules.json`, read as JSON and indexed by `Key`:
  `Source`, `Version` and `Dir` carry the resolutions;
- the plan JSON, whose `module_calls.<name>.version_constraint` gives the
  **written** constraint, distinct from the **resolved** version;
- the lock present in `projet-epingle` with zero mention of the module, and its
  **absence** in `projet-souple`;
- two versions of the same module coexisting in one `modules.json`;
- the `//` then `?ref=` order in the Git address, and the chained `exports.this`
  entry;
- `output -json` for the three labels, and `plan -detailed-exitcode` at 0.

No test reads your `.tf` files.

Stuck? `dsoxlab hint modules-module-registry`.
