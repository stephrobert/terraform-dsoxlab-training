# 🎯 Challenge: update in place or replacement

## Starting point

`challenge/work` holds a configuration full of holes for **a single minimal
VM**: a qcow2 disk copy-on-write from a cloud image, and the domain referencing
it.

**Prerequisites**: `libvirt` reachable at `qemu:///system`, the `default` pool
and `default` network usable, and the cloud image present:

```bash
mkdir -p /var/tmp/dsoxlab-images && curl -fsSL \
  -o /var/tmp/dsoxlab-images/noble-server-cloudimg-amd64.img \
  https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
```

The image is never modified: the VM disk only carries the blocks that change.
That is what lets you recreate a machine in a second rather than copying 600
MiB.

## ✅ Objective

1. **The provider constraint**, which must unambiguously designate the series
   whose schema the code uses.
2. **The domain attributes**: name, hypervisor type, memory and its unit, number
   of vCPUs, and the fact that the machine must be **running**.
3. **Two outputs**: the domain name and its **identifier**.

Then, facing two modifications, **qualify the plan before applying it**: one on
allocated resources, one on the machine identity.

## 🧭 What the lab makes you observe

- **Memory and vCPU change in place.** libvirt can redefine a domain without
  destroying it: the plan announces `["update"]`.
- **The name forces a replacement.** It *is* the domain identity for libvirt:
  changing it does not modify the machine, it builds another one. The plan
  announces `["delete", "create"]` and `replace_paths = [["name"]]`.
- **The identifier proves it afterwards.** libvirt assigns it at creation: a
  modified machine keeps its own, a replaced one receives another.
- **`running` does not prove a VM booted.** A machine with no bootable disk is
  `running` too. What tells them apart is **CPU time**: 0.3 s in one case,
  several seconds in the other.

## 🔍 Validation

```bash
dsoxlab check first-infra-vm-libvirt
```

Seven tests. The fifth and sixth read **plans**, which are predictions. The
seventh **applies** them and compares the domain identifier: that is the only
way to know whether the tool kept its word. The VM and its disk are destroyed on
teardown, whatever happens.
