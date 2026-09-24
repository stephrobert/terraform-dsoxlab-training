# 🎯 Challenge: run the cycle, and prove it

## Starting point

`challenge/work` holds `versions.tf` — **deliberately questionable**, to be
revised — and an **empty** `main.tf`. No `.terraform/`, no state, no lock.

**Prerequisites**: `libvirt` reachable at `qemu:///system`, your user in the
`libvirt` group, the `default` pool defined and started, `terraform` and
`virsh` on the `PATH`. The network is only needed for the first `init`.

**No cloud image to download**: the volume is created empty, and that is enough
to prove the cycle.

## ✅ Objective

1. **Revise the provider constraint** in `versions.tf` so it unambiguously
   installs the `0.9.x` series.
2. A `libvirt` provider at `qemu:///system`.
3. **A single** `libvirt_volume` resource, named `tf-lab-premiere.qcow2`, in the
   `default` pool, in `qcow2` format, with a capacity of **1 GiB**.
4. An `output` exposing the volume **path** on the host, computed from the
   resource attribute and not hard-coded.

Then run the cycle to the end: `init`, a **read** plan, `apply`, and a `destroy`
that leaves nothing.

## 🧭 The `versions.tf` trap

`~> 0.8` **does not forbid** `0.9.x`. The pessimistic operator increments the
**rightmost** component of what is written:

| Constraint | Accepts | Refuses |
|---|---|---|
| `~> 0.8` | `0.8.9`, **`0.9.9`** | `1.0.0` |
| `~> 0.9.0` | `0.9.9` | **`0.10.0`** |

With two components, the **minor** floats. And the 0.9 branch **rewrote the
schema** of almost every resource:

```hcl
# 0.8
size   = 1073741824
format = "qcow2"

# 0.9
capacity      = 1
capacity_unit = "GiB"
target        = { format = { type = "qcow2" } }
```

Letting the minor float means letting the **language** float. Your code applies
today and will break for the colleague whose lock resolved the other series. The
error message will mention an unexpected argument, never a version.

## 🔍 Validation

```bash
dsoxlab check first-infra-first-infrastructure
```

Six tests. The plan is saved then read back as JSON, the state gives the values,
and one check leaves Terraform entirely: `virsh` queries the host directly,
where the state merely reports. The constraint check rebuilds the lock in a
**copy**, because `constraints` is only written when the entry is created. The
last test runs the `destroy` and requires that **nothing survives**, neither in
the state nor on the host.
