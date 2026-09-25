# Produce an Ansible inventory from the state

Terraform provisions, Ansible configures, and the inventory is their **only
point of contact**. Whatever gets lost between the two gets lost there.

The question in this lab is not "how do I write a file from Terraform", it is:
**will this inventory still be true tomorrow?**

## A provisioner produces a file that is right once

The temptation is to write the inventory with a `local-exec` at the end of the
apply. It works on the day, and yet the official documentation ranks these
provisioners as a **last resort**. Three reasons, all verifiable:

- Terraform **cannot model** their behaviour: nothing they do enters the plan;
- they leave **no resource** to inspect in state;
- they only replay when their carrier is **created** or **destroyed**.

The concrete consequence: delete the file, the plan stays at zero changes.
Change an address in the fleet, the plan stays at zero changes. The inventory is
right on the day of the apply, wrong the day after, and **nothing flags it**.

An inventory must be a **managed resource**:

```hcl
resource "local_file" "inventaire" {
  filename = "${path.module}/inventaire.json"
  content  = jsonencode(local.inventaire)
}
```

Delete the file and the plan announces its recreation. Change a value and it
announces an update. Destroy, and it goes with the fleet.

## An explicit type refuses at plan time

```hcl
variable "parc" {
  type = map(object({
    role  = string
    index = number
  }))
}
```

An entry without `index` is rejected **before any provider call**. With `any`,
the same mistake passes the plan and breaks further along, on a message naming
neither the variable nor the offending entry.

That is the difference between an error that says what to fix and an error that
asks for an investigation.

## An address is computed, not copied

```hcl
adresse = cidrhost(var.cidr_de_base, serveur.index)
```

`cidrhost` follows the network. An address copied by hand is right today and
wrong at the first range change, **with nothing to flag it**: the file is still
valid JSON, Ansible still connects, and it lands on a machine that is not the
one you think.

## `jsonencode` rather than concatenation

A hand-built string produces JSON that is *almost* valid. One comma too many, a
quote forgotten inside a hostname, and Ansible returns a parse error that does
not say where.

`jsonencode` escapes what needs escaping, closes what it opens, and returns a
valid document whatever the content. The general rule: **you do not serialise a
format by hand when a function does it**.

## A managed file disappears with the fleet

An inventory that survives destruction points at machines that no longer exist.
Ansible will connect to them, fail, and the message will talk about the network:
people will hunt a breakdown while the real defect is a file that should have
been deleted.

It is the least spectacular half of the subject, and the one that costs the most
time on the day it bites.

## Over to you

```bash
dsoxlab run first-infra-ansible
dsoxlab check first-infra-ansible
dsoxlab hint first-infra-ansible
```

**No cloud, no hypervisor**: the fleet is simulated by resources whose
attributes are only known after creation, like an address allocated by a
scheduler. That is deliberate, a guessable value would prove nothing.

Seven tests. The addresses are not compared against a list written in the test:
they are **recomputed** from the CIDR, two independent computations being worth
more than a constant.

Exam objective targeted: **2e**, supported by **1e**.

Reference: [Terraform and Ansible](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/ansible/)
