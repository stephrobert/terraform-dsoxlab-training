# Update in place or replacement, read it in the plan

## The situation

**Exam objective targeted: 1b `plan`.**

On a virtual machine, some attributes change in place and others destroy then
recreate the machine. The plan says which, before the apply, provided you know
where to look.

## Capability targeted

Declare a minimal libvirt VM, then, faced with a requested change, predict
**before any apply** whether Terraform will perform an in-place update or a
replacement, and prove it from the plan's actions field in JSON rather than from
human output or from an intuition about the attribute involved.

## Where the learner starts

This lab provisions real local resources: it assumes `libvirtd` active on
`qemu:///system`, a usable `default` pool, and a cloud image already downloaded.
No cloud, no cost, a single VM.

`challenge/work` holds a holed configuration for **one minimal VM**: the qcow2
volume derived from the local image, and the domain referencing it, with reduced
memory and a single vCPU on the `default` network. The `???` cover the version
constraint on the `dmacvicar/libvirt` provider, the domain's attributes, and the
outputs exposing the machine's name and id. The directory is bare: no
`.terraform/`, no lock file, no state.

## The state to reach

1. The provider is installed under a version constraint and the lock file pins
   it.
2. The apply creates exactly the expected resources, a volume and a domain, and
   the VM runs.
3. A plan run immediately afterwards announces **no change**.
4. A first change, on allocated resources, produces a plan the learner
   characterises **before** applying it, actions in hand.
5. A second change, on the domain's identity, produces a plan whose actions
   differ from the first: it is no longer the same verb, and the learner
   announces it before applying here too.
6. After that second apply, the domain id recorded in state has **changed**,
   which the first apply did not cause.
7. The `destroy` is clean: nothing left in state, no VM from the lab surviving
   on the host, no volume from the lab left in the pool.

## How it is proven

Nothing is checked by reading back the learner's `.tf` files.

- The plan is saved with `terraform plan -out`, then read back as JSON. In
  `resource_changes`, `change.actions` settles it unambiguously: `["update"]`
  for an in-place update, `["delete","create"]` for a replacement, in which case
  `replace_paths` and `action_reason` are recorded in the same place. That value
  is what gets compared, never a displayed text.
- `terraform show -json` gives managed state after each apply: comparing the
  domain id before and after confirms which operation actually took place.
- `terraform plan -detailed-exitcode` judges convergence: 0 when the
  configuration is stable, 2 while a change is still pending.
- A cross-check outside Terraform, never a source of truth: `virsh list --all`
  shows the VM between the two applies, then nothing after the `destroy`.

## 🎯 Challenge: update in place or replacement

### Starting point

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

### ✅ Objective

1. **The provider constraint**, which must unambiguously designate the series
   whose schema the code uses.
2. **The domain attributes**: name, hypervisor type, memory and its unit, number
   of vCPUs, and the fact that the machine must be **running**.
3. **Two outputs**: the domain name and its **identifier**.

Then, facing two modifications, **qualify the plan before applying it**: one on
allocated resources, one on the machine identity.

### 🧭 What the lab makes you observe

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

### 🔍 Validation

```bash
dsoxlab check first-infra-vm-libvirt
```

Seven tests. The fifth and sixth read **plans**, which are predictions. The
seventh **applies** them and compares the domain identifier: that is the only
way to know whether the tool kept its word. The VM and its disk are destroyed on
teardown, whatever happens.
