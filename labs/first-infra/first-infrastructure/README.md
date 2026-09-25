# First infrastructure: the full cycle, proven

Four commands and the tutorial is over: `init`, `plan`, `apply`, `destroy`.
This lab exists because running them is not the same as **proving** them, and
because a single line of `versions.tf` decides which language you are writing
in without telling you.

It runs on **libvirt**, that is, on real local infrastructure, and this is the
only section of the path where that provider is allowed. No cloud image to
download: a blank volume is enough to prove the cycle.

## `~> 0.8` does not rule out `0.9.x`

This is the trap that motivated the lab, and it comes from an audit of the
guide. The pessimistic operator lets the **rightmost** component written float:

| Constraint | Accepts | Rejects |
| --- | --- | --- |
| `~> 0.8` | `0.8.9`, **`0.9.9`** | `1.0.0` |
| `~> 0.9.0` | `0.9.9` | **`0.10.0`** |

With **two** components, it is therefore the **minor** that floats. Writing
`~> 0.8` while thinking "the 0.8 series" installs 0.9.9 today.

That would be harmless if the versions were alike. But the 0.9 branch of
`dmacvicar/libvirt` **rewrote the schema** of nearly every resource:

```hcl
# 0.8 schema
resource "libvirt_volume" "disque" {
  size   = 1073741824
  format = "qcow2"
}

# 0.9 schema
resource "libvirt_volume" "disque" {
  capacity      = 1
  capacity_unit = "GiB"
  target = {
    format = { type = "qcow2" }
  }
}
```

Letting the minor float means letting the **language** float. Your code applies
on your machine and breaks on the colleague whose lock file kept the other
series, with a message about an unexpected argument and never about a version.

## The lock file keeps the constraint from the day it was born

Measured while writing this lab, and it surprises people:
`.terraform.lock.hcl` writes its `constraints` field when the entry is
**created**, and never updates it afterwards. Neither `init` nor `init -upgrade`
fixes it.

```hcl
provider "registry.terraform.io/dmacvicar/libvirt" {
  version     = "0.9.9"
  constraints = "~> 0.8"   # the original constraint, not the current file's
}
```

A lock file can therefore advertise a constraint your `versions.tf` no longer
carries. Which is why the lab's test rebuilds the lock in a **copy** rather than
reading whichever one is lying around: it checks the **declared** constraint,
not the resolved version, which would be 0.9.9 either way.

## Capacity is not converted for you

Another measurement, and one that costs a cycle to anyone who does not know it:
the provider **does not apply** `capacity_unit` to `capacity`. Declaring
`capacity = 1` with `capacity_unit = "GiB"` creates a volume of **one byte**,
rounded up to a block.

So the lab compares the **effective** capacity read from state, not the two
declared attributes. That is the difference between checking what you wrote and
checking what exists.

## Leaving Terraform to verify Terraform

State is Terraform's **report** on the world. It says what Terraform believes.
Proving a volume exists means asking somebody else:

```console
$ virsh -c qemu:///system vol-list default
 Name                    Path
------------------------------------------------------------
 tf-lab-premiere.qcow2   /var/lib/libvirt/images/tf-lab-premiere.qcow2
```

The lab crosses the two: the path announced by the `output` must be exactly the
one `virsh` lists. A hard-coded output would pass the first check and fall on
the second.

## Cleanup is a test, not a courtesy

The last test runs the `destroy` and demands that **nothing survives**, in state
or on the host. It runs even if the preceding tests failed: without that, a
failed lab would leave a volume behind, and the next lab would pay for it.

## Over to you

```bash
dsoxlab run first-infra-first-infrastructure
dsoxlab check first-infra-first-infrastructure
dsoxlab hint first-infra-first-infrastructure
```

**Prerequisites**: `libvirtd` reachable at `qemu:///system`, your user in the
`libvirt` group, the `default` pool defined and started, `terraform` and `virsh`
on the `PATH`. Network access is only needed for the first `init`.

Exam objective targeted: **1c**, run inside a full cycle **1a** `init`, **1b**
`plan`, **1c** `apply`, **1d** `destroy`.

Reference: [first infrastructure](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/premiere-infrastructure/)
