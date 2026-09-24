# Scenario: the Ansible inventory is a resource, not a side effect

**Exam objective targeted: 2e (declare and consume variables and outputs in complex types), supported by 1e (read state to prove what is actually managed).**

Terraform provisions, Ansible configures, and the inventory is their only point
of contact. The lab imposes the one way of building it that survives the next
plan: a managed resource, derived from state, rather than a file dropped along
the way.

## Capability targeted

Produce, from Terraform, an inventory consumable by a configuration tool, each
value of which derives from state, then demonstrate that this artefact is
tracked: recreated if it disappears, updated if a value changes, deleted on
`destroy`.

That is where the trap lies. The official documentation ranks the `local-exec`
and `remote-exec` provisioners as a last resort: Terraform cannot model their
behaviour, they leave no resource to inspect in state, and they only replay when
their carrier is created or destroyed. The inventory they produce is right on
the day of the apply, wrong the day after.

## Where the learner starts

`challenge/work` holds an incomplete configuration, with no cloud and no
hypervisor: the fleet is simulated by resources whose attributes are only known
after creation, like an address allocated by a scheduler. A complex-typed
variable describes the servers (logical name, role, network index), a base CIDR
is supplied, and no address is hard-coded: a guessable value would prove
nothing. The `???` cover the variable's type, computing addresses with an HCL
function, the `local` provider resource that writes the inventory, and the
output exposing it. The inventory file itself is absent to begin with.

## The state to reach

1. The fleet variable is declared with an explicit structured type, never `any`.
2. Addresses are computed from the base CIDR and each server's index, by an HCL
   function, never copied.
3. A managed resource of the `local` provider writes the inventory Ansible
   expects, groups and host variables included, serialised by a function rather
   than by concatenation.
4. An output exposes the same inventory in structured form.
5. Every value in the generated file is identical to the one in state, including
   a computed attribute impossible to write from memory.
6. Right after the apply, a new plan announces no change.
7. With the file deleted by hand, the next plan announces its recreation; with a
   fleet value changed, it announces an update.
8. After the `destroy`, the inventory file is gone from disk.

## How it is proven

Everything is read from structured state and from the produced artefact, never
from the `.tf`:

- `terraform output -json` returns the inventory as an object, compared value by
  value with the generated file after deserialisation: any discrepancy signs
  manual entry.
- `terraform show -json` exposes the simulated servers' computed attributes;
  those carried by the file must be those in state, which rules out an invented
  value.
- `terraform state list` contains the resource producing the inventory, where a
  provisioner would leave no address to list.
- `terraform plan -detailed-exitcode` exits 0 right after the apply, 2 after the
  file is deleted, 2 after the fleet is changed: a provisioner would stay at 0 in
  both cases.
- After `terraform destroy`, the file is no longer on disk and state is empty.
