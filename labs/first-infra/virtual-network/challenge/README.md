# The dependency Terraform cannot guess

## The situation

**Exam objective targeted: 2d, meta-arguments (`depends_on`).**

The guide creates a NAT network and concludes that a `depends_on` would be
redundant there, since the VM already references the network's attribute. That
is correct: this lab therefore covers the mirror case, where no reference
expresses the dependency any more and Terraform is free to act in the wrong
order.

## Capability targeted

Tell an **implicit** dependency, inferred from a reference to another resource's
attribute, from a **behavioural** dependency invisible in the code, and use
`depends_on` only in the second case: the official documentation makes it a last
resort.

## Where the learner starts

`challenge/work` holds an incomplete configuration: a virtual network whose
forwarding mode and DHCP range are to be filled in, a variable carrying the
network's **name**, and a second block that queries libvirt with that name to
produce a report on disk. That second block consumes the variable, so it
references **no** attribute of the network: nothing in the code tells Terraform
the network must exist first. The directory is otherwise bare: no `.terraform/`,
no state, no dependency lock file.

Machine prerequisites: `libvirtd` active, membership of the `libvirt` group,
access to `qemu:///system`, `virsh` on the PATH, and the `dmacvicar/libvirt`
provider downloadable. No disk image, no VM: the lab stays at network level.

## The state to reach

1. A NAT network exists on the libvirt side, with its gateway, its netmask, its
   DHCP range and autostart disabled.
2. The outputs expose the network's name and gateway by **referencing the
   resource's attributes**, never hard-coded strings.
3. The second block carries an explicit `depends_on` towards the network,
   because it has nothing to reference.
4. The report produced contains what only an **already created** network can
   provide.
5. Immediately after the apply, a new plan announces zero changes, and after the
   destroy nothing remains, in state or in libvirt.

## How it is proven

Everything is read from structured state, never from the learner's `.tf`:

- The plan in JSON exposes the configuration's representation: the outputs carry
  `references` to the network, proof of the implicit dependency.
- That same JSON shows, for the second block, a `depends_on` containing the
  network's address **and** expressions carrying no reference to it whatsoever.
  This is the central proof: the dependency could not be inferred, it was
  declared.
- `terraform show -json` after the apply confirms the recorded forwarding mode
  and DHCP range; `terraform output -json` returns a name and gateway consistent
  with them. The report carries information coming from libvirt: the second
  block therefore ran after creation, or it would have failed.
- A cross-check outside Terraform: `virsh net-list --all` lists the network, and
  `terraform plan -detailed-exitcode` exits **0** right after the apply.
- After the destroy, `terraform show -json` holds no resource any more and
  `virsh net-list --all` no longer knows the network: no libvirt network
  survives the lab.

## 🎯 Challenge: the dependency Terraform cannot guess

### Starting point

`challenge/work` holds an incomplete configuration: a virtual network whose
**forwarding mode** and **DHCP range** are to be filled in, and a second block
producing a report by querying libvirt.

**Prerequisites**: `libvirt` reachable at `qemu:///system`, your user in the
`libvirt` group, `virsh` on the `PATH`. No disk image, no VM: the lab stays at
network level.

### ✅ Objective

1. **The network forwarding mode**: one that gives outbound access without
   exposing the machines.
2. **The DHCP range**, from `.100` to `.200`.
3. **The meta-argument** the second block is missing.
4. **Two outputs**, referencing the resource attributes.

### 🧭 Look closely at the second block

It queries libvirt **with the network name**, taken from the variable. It reads
`var.nom_du_reseau`, not `libvirt_network.lab.name`.

The difference is invisible when reading and decisive when running: Terraform
builds its graph from the **references it finds in expressions**. Here it finds
none. Both blocks are therefore independent in its eyes, and it is **free to run
the report first**.

It does. And when it does, `virsh net-dumpxml` fails on a network that does not
exist yet, the redirection creates an **empty** file, and Terraform announces
`Apply complete!`. Nothing flags it. That is the kind of defect that passes
review and breaks in production one time out of two.

<Aside type="caution" title="The usual rule says the opposite">
Nine times out of ten, a hand-written `depends_on` signals a **missing
reference**: referencing the attribute makes the edge appear, and the
meta-argument becomes a band-aid. This lab is about the tenth time, the one
where there is **nothing** to reference.
</Aside>

### 🔍 Validation

```bash
dsoxlab check first-infra-virtual-network
```

Six tests. The configuration is read from the plan converted to JSON, where
Terraform exposes **what it understood**: the `references` of each output and
the `depends_on` of each resource. One test checks that the `depends_on` is the
**only** thing linking both blocks — placed next to a reference, it would prove
nothing. The network is destroyed on teardown, whatever happens.
