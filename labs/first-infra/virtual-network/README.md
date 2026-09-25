# The dependency Terraform cannot guess

Terraform works out the order of operations by itself, and it does it well. It
builds a graph from the **references it finds in expressions**: if a VM reads a
network's attribute, the network is created first, without anybody having to ask.

Which is why the documentation makes `depends_on` a **last resort**, and why the
guide is right that it would be redundant on a NAT network already referenced.

This lab is about the mirror case: the one where **no** reference expresses the
dependency, and Terraform is therefore free to act in the wrong order.

## Two dependencies that are not alike

**The implicit dependency** comes from a reference. It is visible in the code,
and Terraform sees it too:

```hcl
output "passerelle" {
  value = libvirt_network.lab.addresses[0]   # an edge in the graph
}
```

**The behavioural dependency** is visible nowhere. The block consumes a
**variable**, not an attribute:

```hcl
resource "null_resource" "rapport" {
  provisioner "local-exec" {
    command = "virsh net-dumpxml ${var.nom_du_reseau} > rapport.xml"
  }
}
```

That block needs the network. But it reads nothing from the network: it reads
`var.nom_du_reseau`. To Terraform the two blocks are **independent**, and
nothing stops it running the report first.

## The failure is silent, and that is the point

When it does, `virsh net-dumpxml` fails on a network that does not exist yet,
the redirection creates an **empty** file anyway, and Terraform announces
`Apply complete!`.

Nothing flags it. This is the kind of defect that passes review, works half the
time depending on the order Terraform picks that day, and breaks in production
the day it picks the other one.

The fix is the meta-argument, and this is one of the rare places where it is the
right tool:

```hcl
depends_on = [libvirt_network.lab]
```

## The usual rule says the opposite

Nine times out of ten, a hand-written `depends_on` signals a **missing
reference**. Referencing the attribute makes the edge appear, and the
meta-argument turns into a plaster over code that could have been correct.

So before writing one, the question is always the same: **is there an attribute
I could reference instead?** If yes, reference it. This lab is about the tenth
time, when the answer is no.

## What the plan exposes of Terraform's understanding

The plan converted to JSON does not only show what is about to be done, it shows
**what Terraform understood** of your configuration:

```console
$ terraform show -json tfplan | jq '.configuration.root_module.outputs'
$ terraform show -json tfplan | jq '.configuration.root_module.resources[].depends_on'
```

Each output's `references` prove the implicit dependency. The resource's
`depends_on` proves the declared one. The lab also checks that this `depends_on`
is the **only** thing linking the two blocks: sitting next to a reference, it
would prove nothing at all.

## Over to you

```bash
dsoxlab run first-infra-virtual-network
dsoxlab check first-infra-virtual-network
dsoxlab hint first-infra-virtual-network
```

**Prerequisites**: `libvirt` reachable at `qemu:///system`, your user in the
`libvirt` group, `virsh` on the `PATH`. No disk image, no VM: the lab stays at
network level, and the network is destroyed on exit whatever happens.

Exam objective targeted: **2d**, meta-arguments.

Reference: [creating a virtual network](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/reseau-virtuel/)
