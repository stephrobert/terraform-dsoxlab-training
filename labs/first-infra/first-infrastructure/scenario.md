# Scenario: first infrastructure, the full cycle

**Exam objective targeted: 1c (run `terraform apply` to create infrastructure),
carried out inside a full cycle 1a init, 1b plan, 1c apply, 1d destroy.**

This lab exists so that the Terraform cycle is proven on a real resource, not
recited. The trap comes from an audit of the guide: `~> 0.8` does not rule out
`0.9.x`, it allows the rightmost component to be incremented. Anyone who
believes the opposite writes a `versions.tf` that does not install the provider
they think it does, and their code, written for the 0.9 schema, breaks the
moment a lock file pulls it back to 0.8.

## Capability targeted

Create, observe, then delete real infrastructure with Terraform, knowingly
steering the provider version and reading the result from structured state
rather than from output printed on screen.

## Where the learner starts

The lab runs in `shell` mode, inside `challenge/work`. It is the only section of
the path where the `libvirt` provider is allowed. Prerequisites checked before
anything else: `libvirtd` active and reachable at `qemu:///system`, the user in
the `libvirt` group, the `default` storage pool defined and started, `terraform`
and `virsh` on the `PATH`, and network access for the duration of
`terraform init`.

The directory holds a deliberately questionable `versions.tf`, whose provider
constraint must be reworked, and an empty `main.tf`. No `.terraform/`, no
`terraform.tfstate`, no `.terraform.lock.hcl`. No cloud image to download: the
volume is created blank, which is enough to prove the cycle.

## The state to reach

In `challenge/work`, a configuration declaring:

1. a `terraform` block with a coherent `required_version` and a constraint on
   `dmacvicar/libvirt` that unambiguously installs the `0.9.x` series, the one
   whose schema the code uses;
2. a `libvirt` provider on `qemu:///system`;
3. a single `libvirt_volume` resource, named `tf-lab-premiere.qcow2`, in the
   `default` pool, in `qcow2` format, with a capacity of 1 GiB;
4. an `output` exposing the volume's path on the host, computed from the
   resource attribute rather than hard-coded.

The cycle is carried through to the end: `init`, a plan actually read, `apply`,
then a `destroy` that leaves nothing behind.

## How it is proven

Everything goes through structured state. The learner's `.tf` is never read
back, and no human-facing output is parsed.

- `terraform plan -out=tfplan` then `terraform show -json tfplan`: a single
  entry in `resource_changes[]`, with `change.actions == ["create"]`.
- `terraform show -json` after the apply: `values.root_module.resources[]` holds
  exactly one managed resource of type `libvirt_volume`, whose values confirm
  the name, the `default` pool, the `qcow2` format and the capacity.
- `terraform output -json`: the volume path is present, non-empty, not
  sensitive, and strictly equal to the `path` read from state.
- `terraform plan -detailed-exitcode`: exit code 0, hence no drift.
- The `.terraform.lock.hcl` file does reference `dmacvicar/libvirt` at `0.9.x`.
- A cross-check from outside Terraform: `virsh -c qemu:///system vol-list
  default` lists the volume at the path the output announced.
- Cleanup proven and unconditional: after `terraform destroy -auto-approve`,
  `terraform show -json` no longer returns `values.root_module.resources`, and
  `virsh vol-list default` lists nothing for this lab. The cleanup test runs
  even if the preceding checks failed. Nothing survives the lab.
