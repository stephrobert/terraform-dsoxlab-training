# Bequeath an infrastructure instead of destroying it

A batch of resources reaches end of cycle. Some must **disappear**, others must
**survive** under someone else's responsibility. Both intents go through the same
block, `removed`, and differ by a single argument. Picking the wrong one raises
no error: it deletes the infrastructure.

This tutorial builds the mechanism on a throwaway configuration, then walks to
its boundaries: what it does with a `for_each`, what it refuses to do, and what
it allows that the command line does not.

## The playground

In a directory of its own, outside the challenge:

```hcl
terraform {
  required_version = ">= 1.7"
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

resource "local_file" "inventaire" {
  filename = "${path.root}/inventaire.csv"
  content  = "ref,qte\nvis-8,120\n"
}

resource "local_file" "capteurs" {
  for_each = toset(["nord", "sud"])
  filename = "${path.root}/capteur-${each.key}.txt"
  content  = "capteur ${each.key}\n"
}

resource "random_pet" "demo" {
  length = 2
}

module "legs" {
  source = "./modules/legs"
}
```

The `./modules/legs` module holds a single resource, `random_pet.interne`. After
`terraform init` then `terraform apply`, the state carries five objects:

```text
local_file.capteurs["nord"]
local_file.capteurs["sud"]
local_file.inventaire
random_pet.demo
module.legs.random_pet.interne
```

## One block, two opposite intents

The `removed` block declares that a resource is **no longer managed**. Its
`destroy` argument, inside a `lifecycle` block, decides the fate of the real
object:

```hcl
removed {
  from = local_file.capteurs

  lifecycle {
    destroy = false
  }
}
```

Two rules govern how it is written. First, `from` takes a **reference without
quotes**, like a `moved` block. Second, the matching `resource` block must be
**gone** from the configuration: the two never coexist, and Terraform refuses to
plan while they do, with `Removed resource still exists`.

What really matters sits in the `destroy` argument, and the table reads backwards
if you assume "removed" means "taken out of state":

| Spelling | Planned action | The real object |
| --- | --- | --- |
| without a `lifecycle` block | `delete` | **destroyed** |
| `lifecycle { destroy = true }` | `delete` | **destroyed** |
| `lifecycle { destroy = false }` | `forget` | kept |

**Destruction is therefore the default.** No warning flags it as you write the
block: only the plan says so.

## One block for a whole resource, one action per instance

On a resource multiplied by `for_each` or `count`, a single block is enough, and
the plan details it instance by instance:

```text
 # local_file.capteurs["nord"] will no longer be managed by Terraform, but will not be destroyed
 # local_file.capteurs["sud"] will no longer be managed by Terraform, but will not be destroyed

Plan: 0 to add, 0 to change, 0 to destroy.
```

The plan JSON confirms it, one action per instance:

```json
[
  { "address": "local_file.capteurs[\"nord\"]", "actions": ["forget"] },
  { "address": "local_file.capteurs[\"sud\"]",  "actions": ["forget"] }
]
```

After the `apply`, `capteur-nord.txt` and `capteur-sud.txt` are still on disk,
and both addresses left the state. Note the summary line: `0 to destroy`, while
two objects leave management. **`forget` actions are not counted as
destructions**, which makes sense, but makes the counter misleading on its own.

## What the block refuses: one precise instance

The finest grain of the block is the **whole resource**. Targeting a single
instance fails:

```text
Error: Resource instance keys not allowed

Resource address must be a resource (e.g. "test_instance.foo"), not a
resource instance (e.g. "test_instance.foo[1]").
```

To take out a single key, you need the command, which does accept an indexed
address:

```bash
terraform state rm 'local_file.capteurs["nord"]'
```

And this is where the real trap hides, and it has nothing to do with the state:
while the key remains in the `for_each`, the configuration **asks for the object
again**. The next plan recreates it, and the file you meant to bequeath is
overwritten:

```text
  # local_file.capteurs["nord"] will be created
Plan: 1 to add, 0 to change, 0 to destroy.
```

Removing the key from the collection silences the plan: `No changes. Your
infrastructure matches the configuration.` **Taking one instance out therefore
takes two gestures**, the command then the code alignment, never a single one.

## What the block allows and the command does not do simply

A `removed` block accepts a **whole module**, and returns one `forget` per
resource it contains:

```hcl
removed {
  from = module.legs

  lifecycle {
    destroy = false
  }
}
```

```text
 # module.legs.random_pet.interne will no longer be managed by Terraform, but will not be destroyed
```

This is the clean way to migrate a module to another repository: a single
declaration, reviewed as code, whatever the number of resources inside.

## Unplugging cleanly: destroy-time provisioners

A bequeathed object sometimes needs to be **deregistered** before it goes: out of
an inventory, a directory, a monitoring system. The `removed` block accepts
provisioners for that, and `self` refers to the resource at hand:

```hcl
removed {
  from = local_file.inventaire

  lifecycle {
    destroy = true
  }

  provisioner "local-exec" {
    when    = destroy
    command = "echo desenregistrement ${self.filename} >> journal-migration.txt"
  }
}
```

On `apply`, the provisioner runs before the destruction:

```text
local_file.inventaire: Provisioning with 'local-exec'...
local_file.inventaire (local-exec): Executing: ["/bin/sh" "-c" "echo desenregistrement ./inventaire.csv >> journal-migration.txt"]
local_file.inventaire: Destruction complete after 0s
```

**Only destroy-time provisioners are accepted** in a `removed` block, and a
missing `when` is refused without ambiguity:

```text
Error: Invalid provisioner block

Only destroy-time provisioners are valid in "removed" blocks. To declare a
destroy-time provisioner, use:
    when = destroy
```

## The block is written before it is applied

This is the decisive argument against `terraform state rm`, and it has nothing to
do with syntax. A `removed` block written and pushed for review **describes an
operation that has not happened yet**: `terraform plan` shows it, code review
discusses it, `apply` performs it later. Until it is applied,
`terraform plan -detailed-exitcode` exits with **code 2**, flagging a pending
change.

An imperative command only exists the moment someone types it on their machine:
nothing to review, nothing to discuss, no trace in the repository.

## Your turn

You know that a `removed` block destroys by default, that `destroy = false` turns
the action into a `forget`, that a single block covers every instance of a
`for_each`, that one precise key must go through `terraform state rm` followed by
a collection alignment, that a whole module is bequeathed in one declaration, and
that a destroy-time provisioner lets you unplug an object before letting it go.
The challenge hands you a batch of end-of-life artefacts, each with a different
decision to make.

```bash
dsoxlab run state-removed-block
dsoxlab check state-removed-block
dsoxlab hint state-removed-block
```

Target exam sub-objectives: **1e** (manage state) and **4c** (refactor a
configuration), Professional level.

Reference: [the removed block](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/bloc-removed/)
