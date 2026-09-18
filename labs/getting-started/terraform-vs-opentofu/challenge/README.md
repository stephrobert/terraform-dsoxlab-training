# 🎯 Challenge: make the configuration portable, and see where it stops

## Starting point

`challenge/work` holds **a single file**, `main.tf`, provided and complete: a
two-word `random_pet`, a `local_file` writing its identifier into
`rapport.txt`, a `null_resource` whose trigger depends on it, and a
`nom_animal` output.

There is no `terraform {}` block, no `.terraform/`, no state, no lock.

**This configuration does not apply as is.** The first resource designates its
provider through an alias, `random.principal`, and Terraform answers `Provider
configuration not present`. This is not a flaw to work around: it is the file
the project is missing.

## ✅ Objective

Write `versions.tf`, then apply.

1. A `terraform` block with **`required_version`** and a **`required_providers`**
   explicitly naming `source` and `version` for `random`, `local` and `null`.
2. **Pessimistic** constraints (`~> x.y`): neither pinned nor floating.
3. A **`provider "random"`** block carrying the alias `main.tf` expects.

Then, if `tofu` is installed, pick up the **same state** with it, **on a copy of
the directory**, and look at what it leaves behind.

## 🧭 What the lab makes you observe

- **`tofu` reads terraform's state without destroying anything.** Empty plan,
  same identifier, same provider versions. The announced compatibility exists.
- **But it resolves on `registry.opentofu.org`**, where `terraform` resolves on
  `registry.terraform.io`. The registry prefix is the only thing that changes.
- **And it rewrites `.terraform.lock.hcl`.** After it has run, `terraform` stops
  on `Inconsistent dependency lock file` and demands an `init -upgrade`.
  Portability covers the **state**, not the **lock**.
- **A lock records its constraints only once.** If you ran `init` before writing
  `versions.tf`, `constraints` will stay empty, and even `init -upgrade` will
  not add it. Delete the file and run `init` again.

## 🔍 Validation

```bash
dsoxlab check getting-started-terraform-vs-opentofu
```

Eight tests. The first five play with `terraform` alone: pessimistic constraints
read from a lock rebuilt aside, fully qualified sourcing read from
`version -json`, state, outputs, and idempotence by exit code. The last three
require `tofu` and **skip explicitly** if it is missing: a lab does not fail
anyone over a tool they have not installed. None of them reads your `.tf`.
