# The state lock: where to find it, and how to tell if it is alive

Before any operation that could write the state, Terraform takes a **lock**.
While it is held, another operation that could write is rejected. That is what
stops two concurrent `apply` runs from trampling each other. This tutorial shows
how to observe the mechanism instead of taking it on trust; the challenge will
have you take your own measurements.

## Making the lock observable

A lock lasts as long as the operation. On a trivial configuration the apply ends
in a fraction of a second and there is nothing to see. To observe it, you need a
resource that takes time:

```hcl
resource "terraform_data" "attente" {
  input = "demo"

  provisioner "local-exec" {
    command = "sleep 30"
  }
}
```

`terraform_data` is **built into Terraform**: no provider to download. The
`local-exec` provisioner is used here only as an observation timer, it is not a
recommended way to configure a system.

While that apply runs in a first terminal, a second terminal lets you carry out
the observations.

## Where the lock file lands

With the local backend, the lock is a file placed **next to the state**, not at a
fixed location. Its name is **derived** from the state path: the state file name,
prefixed with a dot, suffixed with `.lock.info`. With the default `path`
(`terraform.tfstate` at the root) that gives `.terraform.tfstate.lock.info` at
the root, hence the common confusion. Move the state and the lock follows:

```hcl
terraform {
  backend "local" {
    path = "stockage/infra.tfstate"
  }
}
```

The lock is then written to `stockage/.infra.tfstate.lock.info`. Its content is a
JSON object whose `Path` field designates the **locked state**, not the lock file
itself. To find it without guessing:

```bash
find . -name '*.lock.info'
```

## Read an exit code, not a message

An error message gets reworded from one release to the next; an **exit code**
compares. It is the only reliable measurement to establish what passes and what
is rejected:

```bash
terraform plan -input=false > /dev/null 2>&1; echo $?
```

`0` means the command completed, `1` that it was rejected. Running each action
that way while a lock is held gives you a table of facts rather than impressions.
Two points deserve attention: not every command takes a lock, and the
`-lock=false` option does not exist on all of them.

## Waiting rather than being rejected

By default a command refused by a lock fails **immediately**: `-lock-timeout` is
`0s`. In continuous integration, two runs that follow each other closely then
reject one another over a few seconds of overlap. A retry window is enough:

```bash
terraform apply -lock-timeout=5m
```

That is the right reflex, far ahead of `-lock=false`, which does not wait: it
removes the protection.

## Held lock and leftover file

The local backend, the documentation says, locks the state "using system APIs".
The real lock is therefore a **system lock** taken by the process, and the kernel
releases it when that process dies, whatever the cause. The `.lock.info` file is
only that lock's calling card: it says who holds what, it holds nothing itself.

The consequence is counter-intuitive and takes a minute to check. Kill a running
apply, see whether the file is still there, run a `plan` again and note its exit
code, then look for the file once more. That is exactly the measurement the
challenge asks for.

## What enables locking on a remote backend

On a remote backend, locking is **not** automatic: it depends on the backend and
on its configuration. The **S3** backend describes it as an **opt-in** feature,
governed by a dedicated argument whose default is `false`. An S3 configuration
that does not set it has no lock at all, even on a recent Terraform release. The
older mechanism based on a **DynamoDB** table still exists but must no longer be
used as the reference. The official S3 backend page names that argument and gives
its default.

## Your turn

You know how to make a lock observable, find it on disk, read its `Path` field,
read an exit code rather than a message, and tell a system lock from a leftover
file. The challenge has you take those measurements and record your findings: the
tests redo the experiment on their side, then compare.

```bash
dsoxlab run state-state-locking
dsoxlab check state-state-locking
dsoxlab hint state-state-locking
```

Target exam objective: **3b** (state locking), Professional level.

Reference: [Locking the Terraform state](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/verrouillage-state/)
