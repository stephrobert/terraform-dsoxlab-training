# Scenario: what Terraform manages, what it merely reads

**Exam sub-objective covered: 2b (data sources), leaning on 5b (provider configuration and versioning).**

Until you have seen a `destroy` erase the managed objects without touching what
the data source was reading, you believe a `data` block is a read-only resource.
This lab forces both real consequences: a data source creates nothing, and it is
re-read on every plan, so it can move a plan although not one line of code has
changed.

## Target capability

Declare the providers of a configuration with a version constraint, then write
in that same configuration `resource` blocks, which Terraform creates and
manages through a full lifecycle, and a `data` block, which Terraform merely
reads. Know how to reference one by `TYPE.NAME.ATTRIBUTE` and the other by
`data.TYPE.NAME.ATTRIBUTE`, and know how to predict what each block becomes
after a `destroy`.

## Where the learner starts

The `challenge/work` directory holds a `catalogue.txt` file already present on
disk, which Terraform never created: it is the "already exists" object of the
scenario. Next to it, an incomplete configuration whose holes bear on what
decides everything: the `required_providers` block, the choice between
`resource` and `data` for each block, and the references between blocks. No
cloud, no VM: the `local`, `null` and `random` providers are enough, `local`
offering both a `local_file` resource and a `local_file` data source. No
`.terraform/`, no state, no lock file.

## The state to reach

1. The three providers are declared in `required_providers` with a pessimistic
   version constraint (`~>`) and installed by `init`.
2. A `data "local_file"` block reads `catalogue.txt`. It neither creates nor
   manages it.
3. A `resource "local_file"` writes a file whose content derives from what the
   data source read, through `data.TYPE.NAME.ATTRIBUTE`: the dependency is
   deduced from the code, never written by hand.
4. A `resource "random_pet"` produces a value known only after creation, and a
   `resource "null_resource"` depends on it through a `triggers` fed both by
   that value and by what the data source read.
5. `output` blocks separately expose a value coming from a resource and a value
   coming from the data source.
6. Right after the apply, a new plan announces zero change.
7. After `destroy`, the files created by Terraform are gone, `catalogue.txt` is
   still there, intact.

## How it is proven

Everything is read from Terraform's machine output, never from the learner's
`.tf`.

- `terraform show -json` separates both natures without ambiguity: the created
  blocks come out as `"mode": "managed"`, the reading block as `"mode": "data"`
  with an address starting with `data.local_file.`. That is the central proof of
  the lab.
- `terraform output -json` shows that the value produced by the resource really
  derives from the content of `catalogue.txt` read by the data source, and that
  both outputs exist.
- Saved plan then read back as JSON (`plan -out` followed by `show -json`):
  right after the apply, no `resource_changes` entry carries an action other
  than `no-op`.
- `terraform plan -detailed-exitcode` exits with 0 right after the apply, then
  with 2 once `catalogue.txt` has been modified by the test without any `.tf`
  being touched: the data source was re-read and the plan moved. A 0 here would
  mean the value being read irrigates nothing.
- After `destroy`, `terraform show -json` reports no managed object any more,
  the managed files are gone from disk, and `catalogue.txt` kept its content
  byte for byte.

The two destructive checks work on a **copy** of the learner's directory: a test
does not break what it measures.
