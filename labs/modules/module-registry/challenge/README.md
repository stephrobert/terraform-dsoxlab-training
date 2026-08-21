# 🎯 Challenge: three projects, one public module, three resolutions

## 🌐 Prerequisite

This lab needs **network access**: the `terraform init` runs reach
`registry.terraform.io` and `github.com`. No cloud account is required, the target
module declares no provider.

## 📦 Starting point

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

## ✅ Objective

Obtain **three different resolutions** of the same module, then prove from
Terraform's artefacts which one got installed where.

## 📋 What you must obtain

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

## ⚠️ The heart of the matter

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

## 🔍 Validation

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
