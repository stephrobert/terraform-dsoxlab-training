# Back up and restore a state, without recreating anything

A state is a file, and a file gets lost, truncated, overwritten by mistake. When
that happens the infrastructure is perfectly fine: only the records are missing.
Repairing therefore means **putting the right state back**, not running an
`apply` that would recreate what already exists.

This tutorial covers the two commands that carry that repair,
`terraform state pull` and `terraform state push`, the two guard rails Terraform
raises against a careless restore, and the safety nets it lays down by itself,
including one almost nobody knows about.

## The playground

In a directory of its own, outside the challenge:

```hcl
terraform {
  required_version = ">= 1.7"
  required_providers {
    local = { source = "hashicorp/local", version = ">= 2.5" }
  }
}

resource "local_file" "releve" {
  filename = "${path.root}/donnees/releve.csv"
  content  = "capteur,valeur\nt1,19\n"
}

resource "local_file" "bulletin" {
  filename = "${path.root}/donnees/bulletin.txt"
  content  = "bulletin hebdomadaire\n"
}
```

A `terraform init` then a `terraform apply` create two files under `donnees/`
and a `terraform.tfstate` at the root.

## `terraform state pull`: photograph the state

The command writes the current state to standard output, **whatever the
backend**. On a remote backend it is the simplest way to get a local copy; on a
local backend it has the merit of going through Terraform rather than through
the filesystem.

```bash
terraform state pull > photo.json
```

Three fields are enough to identify a photo, and they will decide everything:

```json
{
  "lineage": "cf018339-7f2e-b564-8026-b9621939c826",
  "serial": 3,
  "version": 4
}
```

The `lineage` is the **identity of the line**: Terraform draws it at state
creation and never changes it. Two states carrying the same lineage describe the
same infrastructure over time. The `serial` is a **write counter**: it grows on
every state modification, and tells which of two files is the most recent.

## The two safety nets Terraform lays down

The local backend writes a `terraform.tfstate.backup` holding the state **before
the last write**. Many stop there, and that is a mistake: this file is only
refreshed by ordinary operations, `apply` first among them.

A state manipulation command drops a **timestamped** file instead:

```bash
terraform state rm local_file.bulletin
ls terraform.tfstate*
```

```text
terraform.tfstate
terraform.tfstate.1785258572.backup
```

Verified on 1.15.4: after that `state rm`, `terraform.tfstate.backup` did **not
move**, and the timestamped file is the one holding the complete state from
before the command. Practical consequence, worth remembering: **the net that
saves you after a state manipulation is not the one you think**. Since those
files are almost always gitignored, a directory cleanup takes them away without
anyone noticing.

## `terraform state push`: put a state back

The command is the reverse of `pull`. It refuses two situations, and those
refusals are exactly what protects your infrastructure.

**First guard rail, the `serial`.** Pushing a state older than the current one
would drop the writes in between:

```text
Failed to write state: cannot import state with serial 3 over newer state with serial 4
```

**Second guard rail, the `lineage`.** Pushing a state from another project would
break the link between the state and the real infrastructure:

```text
Failed to write state: cannot import state with lineage "11111111-2222-3333-4444-555555555555" over unrelated state with lineage "cf018339-7f2e-b564-8026-b9621939c826"
```

A legitimate restore necessarily hits the **first** of those refusals, since it
puts an earlier state back. That is where `-force` comes in:

```bash
terraform state push -force photo.json
```

There is **no confirmation and no question**: the option overrides both guard
rails, the lineage one included. So check the lineage **before** forcing, never
after.

## What happens to `serial` after a push

This is the most surprising detail, and it cannot be guessed. The restored state
does **not** take over the counter of the state it replaces: it starts again from
its own `serial`, plus one. Force-push a photo at `serial` 1 onto a state at
`serial` 15:

| File | `serial` |
| --- | --- |
| the current state, before | 15 |
| the pushed photo | 1 |
| the current state, after | **2** |

Two consequences, opposite ones. The good one: a `push` always increments, so the
restored state carries a `serial` **greater than the backup's**. A file copied by
hand over `terraform.tfstate` would leave the backup's `serial` untouched: the
shortcut can be read in the file long afterwards.

The bad one, and it is serious on a **shared backend**: your restored state may
carry a `serial` **far below** what other copies have already seen. A colleague
whose local cache knows `serial` 15 now faces a state at 2, which opens the door
to an overwrite in the other direction. After a forced restore on a shared state,
tell the team before anyone pushes.

## Restoring the wrong backup shows up in the plan

A backup with the right lineage but **stale** describes attributes that no longer
match reality. Terraform does not complain at `push` time, it says so at the next
plan:

```text
  # local_file.releve must be replaced
      ~ content = <<-EOT # forces replacement
Plan: 1 to add, 0 to change, 1 to destroy.
```

`terraform plan -detailed-exitcode` then returns **2**. The check is mechanical:
after a restore, a plan that does not exit **0** tells you that you put back a
state that does not describe the infrastructure as it is.

## The reflex that saves you

Before any write into a state, photograph what you are about to replace:

```bash
terraform state pull > avant-intervention.json
```

A `push` cannot be replayed: once the state is overwritten, the only thing left
is what you saved yourself. That photo costs one second and is worth the rest of
the intervention.

## Your turn

You can read a `lineage` and a `serial`, tell apart the two kinds of backups
Terraform lays down, force a `push` knowingly, and recognise a stale backup from
the plan. The challenge hands you a project whose state was amputated, three
candidate backups of which **only one** is restorable, and a perfectly intact
infrastructure that must not be recreated.

```bash
dsoxlab run state-backup-restore-state
dsoxlab check state-backup-restore-state
dsoxlab hint state-backup-restore-state
```

Target exam sub-objective: **1e** (manage state), Associate and Professional
level.

Reference: [back up and restore the state](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/sauvegarder-restaurer-state/)
