# Scenario: read a plan before applying it

**Exam sub-objective covered: Terraform Associate 6d, generate and read an execution plan.**

An already applied configuration must change. Before touching anything, one must
be able to say which of its resources will be updated in place and which will be
destroyed then recreated.

## Target capability

Tell an update in place from a replacement, inside a plan and before any apply,
then execute exactly the plan that was read, thanks to a saved plan applied
non-interactively.

The point is not to type four commands in order. A replacement means an existing
object disappears, with everything it carries, while the human-facing plan
announces both cases in the same block of text. The only reliable reading is the
actions field of the plan converted to JSON.

## Where the learner starts

The `challenge/work` directory holds a configuration using only the `local`,
`null` and `random` providers, plus the built-in `terraform_data`: no virtual
machine, no hypervisor, no cloud access. It deliberately mixes two families of
resources, those whose attribute change is settled by an update in place and
those whose slightest change forces a recreation, both driven by a variables
file.

The learner starts from an uninitialised directory with no state. They must lay
down the reference state, then apply the change requested by the README.

## The state to reach

1. The directory is initialised and the starting configuration is applied: a
   state exists and describes every declared resource.
2. The requested variable value has been changed.
3. A saved plan `tfplan` has been produced with `terraform plan -out=tfplan`,
   and its conversion `plan.json` obtained with `terraform show -json tfplan`.
4. An `analyse.json` file classifies every resource address of the plan into one
   of two categories: update in place, or replacement.
5. The plan has been applied from the file, with no re-plan and no interactive
   confirmation, with `terraform apply tfplan`.
6. After that apply, no change is pending any more.

## How it is proven

The tests run in `challenge/work` and never read the learner's `.tf` files, nor
the human-facing output of the commands.

- The saved plan is reopened by the tool: `terraform show -json tfplan` must
  produce a usable document. A hand-made `tfplan` fails.
- The truth is recomputed from `resource_changes[].change.actions` of that plan,
  then compared to `analyse.json`. An `update` action means update in place; any
  sequence containing both `delete` and `create`, in any order, means
  replacement. The learner's classification must match exactly, address by
  address.
- The final state, read with `terraform show -json`, carries the target values.
- Convergence is proven by `terraform plan -detailed-exitcode` replayed by the
  tests: the expected exit code is `0`, that is an empty diff. Code `2` signals
  a change left pending, code `1` an error.
- That the saved plan was really **consumed** is proven on a copy: replaying
  `terraform apply tfplan` must fail with a stale plan. Had the learner applied
  the configuration another way, that replay would still succeed.
