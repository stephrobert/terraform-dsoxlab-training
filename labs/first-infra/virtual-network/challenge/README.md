# 🎯 Challenge: the dependency Terraform cannot guess

## Starting point

`challenge/work` holds an incomplete configuration: a virtual network whose
**forwarding mode** and **DHCP range** are to be filled in, and a second block
producing a report by querying libvirt.

**Prerequisites**: `libvirt` reachable at `qemu:///system`, your user in the
`libvirt` group, `virsh` on the `PATH`. No disk image, no VM: the lab stays at
network level.

## ✅ Objective

1. **The network forwarding mode**: one that gives outbound access without
   exposing the machines.
2. **The DHCP range**, from `.100` to `.200`.
3. **The meta-argument** the second block is missing.
4. **Two outputs**, referencing the resource attributes.

## 🧭 Look closely at the second block

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

## 🔍 Validation

```bash
dsoxlab check first-infra-virtual-network
```

Six tests. The configuration is read from the plan converted to JSON, where
Terraform exposes **what it understood**: the `references` of each output and
the `depends_on` of each resource. One test checks that the `depends_on` is the
**only** thing linking both blocks — placed next to a reference, it would prove
nothing. The network is destroyed on teardown, whatever happens.
