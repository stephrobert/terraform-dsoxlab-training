# 🎯 Challenge: constrain the CLI, lock the providers

## Starting point

`challenge/work` holds only an **empty** `main.tf`. No `.terraform/`, no
`.terraform.lock.hcl`, no downloaded provider.

No VM, no cloud: the network is only needed to download the providers.

## ✅ Objective

In `challenge/work`:

1. **A `terraform {}` block** carrying a `required_version` your CLI satisfies,
   and a `required_providers` declaring `hashicorp/local`, `hashicorp/null` and
   `hashicorp/random` with **explicit** constraints.
2. **One resource from each** of those three providers.
3. **`terraform init`** succeeding, producing `.terraform.lock.hcl` with the
   three providers and their checksums.
4. **`terraform providers lock`** re-run for **at least two platforms**.
5. **The configuration applied**, state converged.

In an `echec-version/` subdirectory:

6. **A minimal configuration** whose `required_version` **cannot** be satisfied
   by your CLI.

## 🧭 Three things people conflate

**`required_version` does not apply to providers.** It constrains the CLI alone.
Pinning Terraform pins nothing it downloads: `required_providers` does that, and
the lock file freezes it.

**It is not the same as a `.terraform-version`.** That one says which CLI to
**install** on your machine. `required_version` says which CLI is allowed to
**run** this configuration, and it travels with it in the repository.

**A lock file is meant to be committed.** It is not a cache. It is what
guarantees your colleague gets the same versions as you, and it can only do that
from inside the repository.

## ⚠️ The trap that only shows elsewhere

Lock checksums are **per platform**. A lock created on Linux holds none for
macOS: your colleague's `init` will fail on a file you did commit, and the
message will mention a missing checksum, never a platform.

```bash
terraform providers lock -platform=linux_amd64 -platform=darwin_arm64
```

To be re-run **every time a constraint changes**.

## 🔍 Validation

```bash
dsoxlab check getting-started-install-terraform
```

No test opens your `.tf` files. The central proof is the lock one: the
`.terraform/` directory is deleted, `init` is re-run, and `provider_selections`
must stay **strictly identical**. If the versions moved, the lock would be
pointless.

The failing subdirectory is judged on its **exit code**, not its message: text
changes between versions.

Stuck? `dsoxlab hint getting-started-install-terraform`.
