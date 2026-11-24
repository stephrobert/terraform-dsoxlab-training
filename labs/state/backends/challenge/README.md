# One backend, two environments, zero hardcoded path

## The situation

**Target exam objective: 3b (remote state).**

The `backend` block accepts **no named value**: no variable, no local, no data source attribute. That is the trap of this lab, and the reason for **partial configuration** and `-backend-config`.

## Target capability

Configure a backend in **partial configuration** (the block sets no `path`), feed it with a `-backend-config` file per environment, and **migrate** an existing state to this backend **without recreating it**.

## Where the learner starts

`challenge/work` holds an appliable project, in top-level files (the runtime flattens subdirectories):

- `versions.tf`, `main.tf`: complete, do not modify. `main.tf` has a `random_pet` and a `local_file`, whose state must migrate.
- `variables.tf`: a `chemin_state` variable declared, the **trap**: using it in the backend block makes `init` fail on `Variables not allowed`.
- `dev.local.tfbackend`: one line, `path = "???"`.
- `backend.tf` and `prod.local.tfbackend`: **absent**, to be created.

The test **orchestrates** the migration like a real switch to a backend: it first applies with the **implicit local backend** (no `backend.tf`), captures the `lineage`, then adds `backend.tf` and runs `terraform init -migrate-state -backend-config=dev.local.tfbackend`.

## The target state

1. A `backend "local"` block exists and sets **no** `path`: reinitialized without `-backend-config`, Terraform resolves `path` to `null`.
2. Two partial configurations point at two locations: `etat/dev/terraform.tfstate` and `etat/prod/terraform.tfstate`.
3. After migrating to `dev`, the chosen backend is `local` and its resolved `path` is the dev one.
4. The state **migrated**, it was not recreated: **same `lineage`** as at the start, and the two resources in `mode: managed`.
5. `etat/dev/terraform.tfstate` exists on disk.
6. No pending change: `plan -detailed-exitcode` returns `0`.

## How it is proven

The tests never open a `.tf`. They read what Terraform writes.

1. **Migration, not recreation**: `terraform state pull` before and after; the `lineage` is **identical**. A from-scratch `apply` would produce a new lineage and fail here. `show -json` lists exactly two `mode: managed` resources.
2. **Resolved backend**: `.terraform/terraform.tfstate` carries `backend.type = local` and `backend.config.path = etat/dev/terraform.tfstate`. Its absence would prove a backend left implicit.
3. **Partial config**: in a **copy** of the directory, `terraform init` **without** `-backend-config` resolves `path` to `null` (a hardcoded path would show up here), and `init -reconfigure -backend-config=prod.local.tfbackend` resolves to `etat/prod`. The same block, two locations: that is the proof of partialness.
4. **Idempotence**: `plan -detailed-exitcode` returns `0`.

Reference: https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/backends-terraform/ (in French)

## 🎯 Challenge: partial backend and state migration

### ✅ Objective

In `challenge/work`, switch the project from the **implicit** local backend to a
**parameterized** `local` backend, migrating the state. To do:

1. **create `backend.tf`** with a backend block in **partial configuration**:
   ```hcl
   terraform {
     backend "local" {}
   }
   ```
   (no `path` here, and definitely not `var.chemin_state`: the block refuses named
   values);
2. fill the `path` of **`dev.local.tfbackend`**:
   `path = "etat/dev/terraform.tfstate"`;
3. **create `prod.local.tfbackend`** with `path = "etat/prod/terraform.tfstate"`.

The test first applies with no backend, then migrates with
`terraform init -migrate-state -backend-config=dev.local.tfbackend`.

### 🔍 Validation

`dsoxlab check state-backends` proves, on JSON:

- the **`lineage`** is the same before and after: the state **migrated**, was not
  recreated; two `mode: managed` resources;
- `.terraform/terraform.tfstate` carries `backend.type = local` and
  `backend.config.path = etat/dev/terraform.tfstate`;
- the config is **partial**: in a copy, `init` without `-backend-config` resolves
  `path` to `null`, and `-backend-config=prod...` resolves to `etat/prod`;
- idempotence (`plan -detailed-exitcode` = 0).

Stuck? `dsoxlab hint state-backends`.
