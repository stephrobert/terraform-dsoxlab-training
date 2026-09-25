# Scenario: what Terraform manages, and what it merely reads

**Exam objective targeted: 2b (data sources), supported by 5b (provider configuration and versioning).**

Until you have seen a `destroy` wipe the managed objects without touching what the data
source was reading, you believe a `data` block is a read-only resource. This lab imposes
both real consequences: a data source creates nothing, and it is re-read on every plan, so
it can move a plan although the code has not moved a line.

## Capability targeted

Declare a configuration's providers with a version constraint, then write, in the same
configuration, `resource` blocks that Terraform creates and manages with a full lifecycle,
and a `data` block that Terraform merely reads. Know how to reference one through
`TYPE.NAME.ATTRIBUTE` and the other through `data.TYPE.NAME.ATTRIBUTE`, and be able to
predict what each block becomes after a `destroy`.

## Where the learner starts

The `challenge/work` directory holds a `catalogue.txt` file already present on disk, which
Terraform never created: it is the scenario's "already exists" object. Next to it, an
incomplete configuration whose holes cover what decides everything: the
`required_providers` block, the choice between `resource` and `data` for each block, and
the references between blocks. No cloud, no VM: the `local`, `null` and `random` providers
are enough, `local` providing both a resource and a `local_file` data source. No
`.terraform/`, no state, no lock file.

## The state to reach

1. The three providers are declared in `required_providers` with a pessimistic version
   constraint (`~>`) and installed by `init`.
2. A `data "local_file"` block reads `catalogue.txt`. It neither creates nor manages it.
3. A `resource "local_file"` writes a file whose content derives from what the data source
   read, through `data.TYPE.NAME.ATTRIBUTE`: the dependency is inferred from the code,
   never written by hand.
4. A `resource "random_pet"` produces a value known only after creation, and a
   `resource "null_resource"` depends on it through `triggers` fed both by that value and
   by what the data source read.
5. Outputs expose separately a value coming from a resource and a value coming from the
   data source.
6. Right after the apply, a new plan announces zero changes.
7. After `destroy`, the files Terraform created are gone, and `catalogue.txt` is still
   there, intact.

## How it is proven

Everything is read from Terraform's machine output, never from the learner's `.tf`.

- `terraform show -json` separates the two kinds unambiguously: created blocks come out as
  `"mode": "managed"`, the reading block as `"mode": "data"` with an address starting with
  `data.local_file.`. That is the lab's central proof.
- `terraform output -json` shows the value produced by the resource does derive from the
  contents of `catalogue.txt` read by the data source, and that both outputs exist.
- `terraform plan -detailed-exitcode` exits 0 right after the apply, then 2 once
  `catalogue.txt` has been modified by the test without any `.tf` being touched: the data
  source was re-read and the plan moved. A 0 here means the value read feeds nothing.
- After `destroy`, `terraform show -json` reports no object, the managed files are gone
  from disk, and `catalogue.txt` has kept its content byte for byte. That destroy runs in a
  copy of the directory, so the lab stays replayable.
