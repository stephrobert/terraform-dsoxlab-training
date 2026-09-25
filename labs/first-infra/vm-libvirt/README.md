# Update in place or replacement: read it in the plan

Changing a virtual machine is not one operation, it is two. Depending on the
attribute you touch, Terraform redefines the machine without interrupting it, or
destroys it to build another one. The difference is visible **before** the
apply, if you know where to look, and it is expensive on the day you learn it in
production.

## The plan carries a verb, not a colour

Human output uses `~` and `-/+` markers that people skim past. The saved plan,
read back as JSON, carries a field nobody skims:

```console
$ terraform plan -out=tfplan
$ terraform show -json tfplan | jq '.resource_changes[].change.actions'
["update"]
```

Three values say everything:

| `change.actions` | What is about to happen |
| --- | --- |
| `["update"]` | in-place update, the machine survives |
| `["delete", "create"]` | replacement, the machine is rebuilt |
| `["create", "delete"]` | replacement too, but the new one first (`create_before_destroy`) |

When it is a replacement, the plan also says **which attribute** forced it, in
the same place:

```json
"actions": ["delete", "create"],
"replace_paths": [["name"]]
```

Measured on this lab: `replace_paths` is `null` for a memory or vCPU update, and
`[["name"]]` for a name change. That is the answer to "what in my change forced
this", and it lives in the plan, not in the documentation.

## What updates, and what rebuilds

On a libvirt domain the line is sharp, and this lab has you observe it from both
sides:

- **memory and vCPUs update in place.** libvirt can redefine a domain without
  destroying it;
- **the name forces a replacement.** It *is* the domain's identity: changing it
  does not modify the machine, it builds another one.

The general rule behind that particular case: an attribute that takes part in an
object's **identity** at the provider cannot be updated. The provider marks it
`ForceNew`, and the plan turns that into `delete` + `create`.

## The id settles it afterwards

A prediction stays a prediction. What proves which operation actually happened
is the id libvirt assigns **at creation**:

```console
$ terraform show -json | jq -r '.values.root_module.resources[]
    | select(.type=="libvirt_domain") | .values.id'
```

An updated machine keeps its own. A replaced machine receives a different one.
The lab records both and compares them: that is the only way to know whether the
tool kept the promise the plan made.

## `running` does not prove a VM booted

Measured while writing this lab, and it holds beyond libvirt: a machine with no
bootable disk is `running` as well. The "running" state says a process exists,
not that a system started.

What tells them apart is **CPU time consumed**: around 0.3 seconds for a machine
vainly looking for a disk, several seconds for one that actually boots.

Which is why the disk is a **copy-on-write derivative** of the cloud image
rather than a blank volume: the image is never modified, the VM's disk only
carries the blocks that change, and rebuilding a machine costs one second
instead of copying 600 MiB.

## Over to you

```bash
dsoxlab run first-infra-vm-libvirt
dsoxlab check first-infra-vm-libvirt
dsoxlab hint first-infra-vm-libvirt
```

**Prerequisites**: `libvirt` reachable at `qemu:///system`, the `default` pool
and `default` network usable, and the cloud image present:

```bash
mkdir -p /var/tmp/dsoxlab-images && curl -fsSL \
  -o /var/tmp/dsoxlab-images/noble-server-cloudimg-amd64.img \
  https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
```

The VM and its disk are destroyed on exit, whatever happens.

Exam objective targeted: **1b**.

Reference: [creating a VM with libvirt](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/vm-libvirt/)
