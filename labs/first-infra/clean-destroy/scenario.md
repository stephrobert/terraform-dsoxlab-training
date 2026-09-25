# Scenario: destroying without losing state

**Exam objective targeted: 1d (`terraform destroy`), supported by 1e (inspect state).**

Destroying is not a single gesture: full destroy, targeted destroy, refusal
raised by `prevent_destroy`, a resource removed from code that disappears
without anybody asking. And a successful destroy empties state, it does not
delete the file.

## Capability targeted

Steer a destruction: **block** it with a guard rail, **target** it on part of the
graph, **trigger** it by removing code, then prove from structured state what is
gone and what remains. Know that a destruction plan can be read before it runs,
and that `prevent_destroy` protects nothing any more once the resource block
leaves the configuration.

## Where the learner starts

`challenge/work` holds a configuration built on the `random`, `local` and `null`
providers: no cloud, no VM, no network call, everything deterministic and
replayable. Three resources form an explicit dependency chain: a `random_pet`
gives a suffix, a `local_file` writes an inventory referencing that suffix, a
`null_resource` declares `triggers` computed from the file path. A fourth
resource, independent of the other three, acts as a witness. The directory is
bare: no `.terraform/`, no state, and an incomplete `lifecycle` block carries
`???` on the resource to protect.

## The state to reach

1. The configuration is initialised then applied: all four resources exist in
   state.
2. The `local_file` is protected by a `lifecycle { prevent_destroy = true }`: a
   full `terraform destroy` **fails** without destroying anything, exit code kept
   in `artefacts/rc-prevent-destroy.txt`.
3. A destruction plan exported to JSON under `artefacts/plan-destroy.json`
   announces the removal of all four resources, without destroying any.
4. Once the protection is lifted, a **targeted destroy** removes only the
   `null_resource`: the three other resources stay managed.
5. The witness resource is **removed from the code**, then an `apply` is run:
   Terraform destroys it because it is no longer declared.
6. A full `destroy` empties state of the rest, and `terraform.tfstate` **still
   exists** on disk, with no managed resource left.

## How it is proven

No test reads back the learner's `.tf`, and none parses human output.

- The guard rail: a **non-zero exit code** recorded in
  `artefacts/rc-prevent-destroy.txt`, cross-checked with a `terraform show -json`
  showing all four resources still managed.
- The **complete plan**: in `artefacts/plan-destroy.json`, the four addresses
  carry the `delete` action. Addresses are counted, not merely the file's
  existence: a plan taken before the protection was lifted fails, writes its file
  anyway, and only puts three resources in it.
- The **targeting** and the **removal from code**: through the addresses
  remaining in `terraform show -json`, first the `null_resource`, then the
  witness.
- The **final state**, on two distinct points: the state file is present and
  remains valid JSON with its version and lineage fields, and
  `terraform show -json` exposes nothing under `values.root_module`. Confusing
  the two is the lab's trap.
