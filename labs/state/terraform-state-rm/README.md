# Stop managing a resource, without destroying it

A resource changes hands: it moves to another team, another repository, a tool
that is not Terraform. The object must keep existing, but Terraform must stop
tracking it. The need is mundane, and it is also the most dangerous operation on
a state file: depending on the mechanism you pick, the same intent either keeps
the object or deletes it.

There are two ways. `terraform state rm` drops an entry from the state, right
now, from your machine. The `removed` block, available since Terraform **1.7**,
declares the removal in code. This tutorial shows both on a throwaway
configuration, before the challenge asks you to use each one where it belongs.

## The playground

Create a directory of its own, outside the challenge, with this configuration:

```hcl
terraform {
  required_version = ">= 1.7"
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

resource "local_file" "meteo" {
  filename = "${path.root}/meteo.csv"
  content  = "ville,temp\nlille,12\n"
}

resource "local_file" "lot" {
  count    = 3
  filename = "${path.root}/lot-${count.index}.txt"
  content  = "lot ${count.index}\n"
}

resource "random_pet" "demo" {
  length = 2
}
```

A `terraform init` then a `terraform apply` create five objects, which the state
lists by address:

```bash
terraform state list
```

```text
local_file.lot[0]
local_file.lot[1]
local_file.lot[2]
local_file.meteo
random_pet.demo
```

## `terraform state rm`: forget it right now

The command drops an entry from the state and **never touches** the real object.
Try it dry first, a good habit on a shared state:

```bash
terraform state rm -dry-run local_file.meteo
```

```text
Would remove local_file.meteo
```

Then for real:

```bash
terraform state rm local_file.meteo
```

```text
Removed local_file.meteo
Successfully removed 1 resource instance(s).
```

The file is still there with its original content: `cat meteo.csv` returns
`ville,temp` then `lille,12`. Terraform simply stopped knowing about that object.

The signature takes **several addresses** in a single call, and it reaches down
to the **instance** when a resource carries `count` or `for_each`:

```bash
terraform state rm 'local_file.lot[0]' 'local_file.lot[2]'
```

```text
Removed local_file.lot[0]
Removed local_file.lot[2]
Successfully removed 2 resource instance(s).
```

Quote the brackets, under zsh as under bash: unquoted, the shell tries to read
them as a glob and the command never receives the address. An address that
matches nothing is not silent, it exits with **code 1**:

```text
Error: Invalid target address

No matching objects found. To view the available instances, use "terraform
state list". Please modify the address to reference a specific instance.
```

## The orphan: the trap of the imperative way

The entry is gone, but the `resource` block is still in the code. To Terraform
the reading is unambiguous: the configuration describes an object the state does
not know about, so it must be created.

```bash
terraform plan
```

```text
  # local_file.meteo will be created
Plan: 1 to add, 0 to change, 0 to destroy.
```

That is the trap of the imperative way, and it bites harder on real
infrastructure: the next `apply`, run by anyone, recreates an object that
already exists. The removal is only complete once the `resource` block is gone
from the code, **along with every expression still referencing its attributes**
elsewhere in the configuration. A single forgotten reference is enough to fail
the plan.

Order matters: remove from the state **then** clean the code. The other way
around, the configuration describes one object less than the state, and
Terraform plans a destruction.

## The `removed` block: same removal, but versioned

The block declares the intent in code, where it is reviewed, discussed and
replayed identically by the whole team. The address is written as a reference,
without quotes:

```hcl
removed {
  from = random_pet.demo

  lifecycle {
    destroy = false
  }
}
```

One condition is mandatory: the matching `resource` block must be **gone** from
the configuration. The two never coexist, and Terraform refuses to plan while
they do:

```text
Error: Removed resource still exists

  on main.tf line 20:
  20: resource "random_pet" "demo" {

This statement declares that random_pet.demo was removed, but it is still
declared in configuration.
```

Once the `resource` block is gone, the plan announces a removal without
destruction. Note the leading marker, a dot, distinct from the `-` of a deletion:

```text
 # random_pet.demo will no longer be managed by Terraform, but will not be destroyed
 # (destroy = false is set in the configuration)
 . resource "random_pet" "demo" {
        id        = "intent-stallion"
        # (2 unchanged attributes hidden)
    }

Plan: 0 to add, 0 to change, 0 to destroy.

Warning: Some objects will no longer be managed by Terraform

If you apply this plan, Terraform will discard its tracking information for
the following objects, but it will not delete them:
 - random_pet.demo
```

The `apply` confirms nothing moved on the infrastructure side:
`Apply complete! Resources: 0 added, 0 changed, 0 destroyed.` The object left
the state, it did not leave existence.

## A `removed` block destroys by default

Here is the point that costs the most, and that the syntax never signals. Drop
the `lifecycle` block, keep the rest:

```hcl
removed {
  from = local_file.lot
}
```

Terraform accepts it **without the slightest warning**, and plans the opposite of
what the word "removed" suggests:

```text
  # local_file.lot[2] will be destroyed
  # (because local_file.lot is not in configuration)
  - resource "local_file" "lot" {
      - filename             = "./lot-2.txt" -> null
      - id                   = "f62fb50f2c6a58ed24da0bd2901ea4151b9a1890" -> null
    }

Plan: 0 to add, 0 to change, 3 to destroy.
```

On `apply`, the three files leave the disk: `Apply complete! Resources: 0 added,
0 changed, 3 destroyed.` Destruction is the block's **default** behaviour, and
`destroy = false` is what waives it. Three spellings, two outcomes:

| Spelling | Planned action | The real object |
| --- | --- | --- |
| `removed` without a `lifecycle` block | `delete` | **destroyed** |
| `removed` with `lifecycle { destroy = true }` | `delete` | **destroyed** |
| `removed` with `lifecycle { destroy = false }` | `forget` | kept |

## Machine proof: `forget` versus `delete`

Human output reads poorly in review and does not automate. A saved plan turned
into JSON settles it in one word:

```bash
terraform plan -out=oubli.tfplan
terraform show -json oubli.tfplan
```

```json
[
  { "address": "local_file.lot[0]", "actions": ["create"] },
  { "address": "random_pet.demo",   "actions": ["forget"] }
]
```

`forget` is the action of a removal without destruction, a `delete` in the same
place is a deletion. This is the check to run in review or in CI before any
`apply` carrying a `removed` block, all the more so as the official JSON format
page does not list `forget` among the possible actions yet: the value is
observed at run time.

## What `from` accepts, and what it rejects

The two mechanisms do not share the same granularity. An instance key, which
`terraform state rm` handles without complaining, is rejected by the block:

```text
Error: Resource instance keys not allowed

  on oubli.tf line 2, in removed:
   2:   from = local_file.lot[1]

Resource address must be a resource (e.g. "test_instance.foo"), not a
resource instance (e.g. "test_instance.foo[1]").
```

A `removed` block therefore covers the **whole** resource, every instance
included. It does accept a **whole module**, which has no simpler equivalent:

```hcl
removed {
  from = module.stock

  lifecycle {
    destroy = false
  }
}
```

The plan then returns one `forget` per resource inside the module, here
`module.stock.random_pet.interne`.

## Which one, and when

| Situation | Method |
| --- | --- |
| One-off removal, a precise instance (`[1]`, `["web"]`) | `terraform state rm` |
| Removal that must be reviewed, traced, replayed by the team | `removed` block |
| Migrating a module to another repository | `removed` block on the module |
| Terraform older than 1.7 | `terraform state rm`, the only option |

HashiCorp recommends the `removed` and `import` blocks for **any new
migration**: an imperative command leaves no trace in the repository, where a
versioned block can be read again and replayed. Once the removal is applied,
keeping the block is harmless, the next plan returns `No changes`: deleting it
is housekeeping, not an obligation.

## Your turn

You know that removing an entry from the state destroys nothing, that a resource
removed from the state but still declared becomes an orphan the plan wants to
recreate, that the `removed` block requires the `resource` block to be gone
first, that its default is to **destroy** and that `destroy = false` produces a
`forget`. The challenge hands you a four-resource project where two of them must
stop being managed without their files disappearing, one by each way.

```bash
dsoxlab run state-terraform-state-rm
dsoxlab check state-terraform-state-rm
dsoxlab hint state-terraform-state-rm
```

Exam sub-objective: **1e** (inspect and manipulate state), Associate level.

Reference: [terraform state rm](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-rm/)
