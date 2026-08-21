# Scenario: stop managing a resource without destroying it

**Target exam sub-objective: 1e, manage state (removal, orphaned resources, reconciliation).**

Removing a resource from the state does not destroy it: it becomes an orphan, and the next plan will want to recreate it. This lab makes that trap happen, then has the same removal performed the declarative way, the one HashiCorp now recommends for any new migration. That second way carries its own, costlier trap: a `removed` block **destroys by default**.

## Target capability

Take a resource out of Terraform's control without touching the real object, both ways: the `terraform state rm` command, then a `removed` block with `lifecycle { destroy = false }`. And know that this guard rail is not decorative: neither the `lifecycle` block nor the `destroy` argument is mandatory, all three spellings plan without error, and two of them **delete the infrastructure**.

## Where the learner starts

The `challenge/work` directory is a `shell` lab: `local` and `random` providers only, no virtual machine, no cloud access.

It holds two files, and no state:

- `main.tf`, complete and applicable as is, with four resources: `local_file.rapport` writing `rapport.txt` (target of the imperative way), `local_file.archive` writing `archive.txt` (target of the declarative way), then `local_file.conserve` and `random_pet.identifiant`, two witnesses that must stay managed from start to finish;
- `retrait.tf`, carrying a `removed` block **shipped commented out** and holed by two `???`: the target address and the value of `destroy`. Since the block is commented, the configuration applies as is: the first `terraform init` then `terraform apply` is on the learner, and it is what sets the four-resource starting state.

## The state to reach

1. The project has been applied: the three files `rapport.txt`, `archive.txt` and `conserve.txt` exist with their original content.
2. `local_file.rapport` left the state through `terraform state rm`, and its `resource` block is gone from `main.tf`, along with any expression referencing its attributes elsewhere.
3. `retrait.tf` carries a `removed` block, uncommented and completed, targeting `local_file.archive` with `destroy = false`, and the matching `resource` block was removed from `main.tf`. The two cannot coexist: Terraform refuses to plan with `Removed resource still exists`.
4. That declarative removal has been applied: `local_file.archive` left the state.
5. `rapport.txt` and `archive.txt` are still on disk, content intact. That is the only outcome telling a removal from a destruction.
6. Both witnesses are still in the state, in `mode: managed`.
7. No change is pending anymore.

## How it is proven

Tests run inside `challenge/work`, never open the learner's `.tf` files and never parse human-facing output.

- `terraform show -json`: the `mode: managed` addresses of the root module are **exactly** `local_file.conserve` and `random_pet.identifiant`. Both targets must be absent, both witnesses present.
- `rapport.txt` and `archive.txt` are read from disk and compared with their original content. A learner who let Terraform destroy an object, typically by forgetting `destroy = false`, fails here and nowhere else.
- `terraform plan -detailed-exitcode` replayed by the tests returns 0. A code 2 would signal either a `resource` block left in the code (the removed resource would be an orphan, and Terraform would want to **recreate** it), or a `removed` block never applied.
- The imperative trap is proven by execution, not by an artefact the learner would have to think of producing: the test copies `challenge/work` into a temporary directory, redeclares `local_file.rapport` there, saves a plan and requires `actions == ["create"]`.
- The declarative trap is proven the same way, on a witness and in a copy: a `removed` block **without** `lifecycle` must plan `["delete"]`, and the same block **with** `destroy = false` must plan `["forget"]`. These two tests do not grade the learner's work, they verify that the behaviour taught by the lab is still Terraform's. If they turn red, the lab needs reviewing, not the submission.
- The `forget` action is not documented in the official JSON format: it is observed by execution on Terraform 1.15.4, and that measurement is what stands.
