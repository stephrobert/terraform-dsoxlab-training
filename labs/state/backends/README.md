# Terraform backends: where the state lives, and how to configure it

A **backend** decides **where** Terraform stores the state and **how** it locks
it. By default it is the **`local`** backend: a `terraform.tfstate` in the current
directory. On a team, you move it to a **remote** backend (S3, GCS, HCP…) to share
and lock the state. This tutorial shows the configuration mechanics, its traps, and
migration; the challenge makes you prove it on a parameterized `local` backend.

## The trap: the backend block accepts no named value

The `backend` block is read **very early**, before variables are evaluated. It
therefore **accepts no named value**: no `var.`, no `local.`, no data source
attribute. This fails:

```hcl
terraform {
  backend "local" {
    path = var.chemin_state   # Error: Variables not allowed
  }
}
```

That is exactly why **partial configuration** exists.

## Partial configuration and `-backend-config`

You leave the backend block **incomplete**, and supply the rest at `init`:

```hcl
terraform {
  backend "local" {}   # partial: no path here
}
```

```bash
terraform init -backend-config=dev.local.tfbackend
```

The `dev.local.tfbackend` file carries `path = "etat/dev/terraform.tfstate"`. One
**file per environment** (`dev`, `prod`…) feeds the **same** backend block without
ever hardcoding the path. Reinitialized **without** `-backend-config`, a partial
block resolves its values to `null`: that is the proof it is truly partial.

Terraform records the **resolved** configuration in `.terraform/terraform.tfstate`
(`backend.type` and `backend.config`), a local file that is not the state itself.

## Migrating an existing state: `-migrate-state`

When you add or change a backend on an **already applied** project, Terraform
offers to **migrate** the state, without recreating it:

```bash
terraform init -migrate-state -backend-config=dev.local.tfbackend
```

The state keeps its **`lineage`**: that is the proof of a migration, not a fresh
apply (which would produce a different lineage). Tell it apart from
**`-reconfigure`**, which **ignores** the existing state and starts fresh on the
new backend, with no migration. Picking the wrong one is a classic source of lost
state.

## Your turn

You know that the backend block refuses named values, that partial configuration
plus `-backend-config` gives one file per environment, that a partial block
resolves to `null` without config, and that `-migrate-state` moves a state while
keeping its `lineage`. The challenge makes you switch a project from the implicit
local backend to a parameterized `local` backend, migrating the state.

```bash
dsoxlab run state-backends
dsoxlab check state-backends
dsoxlab hint state-backends
```

Target exam objective: **3b** (remote state), Professional level.

Reference: [Terraform backends](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/backends-terraform/)
