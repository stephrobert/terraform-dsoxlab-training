# Scenario: arbitrating between workspaces and separate configurations

**Exam sub-objective covered: 3d.**

The official documentation is clear: workspaces suit light variations of one
infrastructure, but not deployments requiring distinct credentials or access
controls, nor decomposing a system into components. This lab puts the decision on
the learner, then makes them pay the price of the split: two separate
configurations no longer talk to each other, their data must be wired back.

## Target capability

Recognise, on a given configuration, which of the two strategies applies, then
split the part that no longer belongs in workspaces into two root configurations
with distinct states, and rewire the dependency between them through
`terraform_remote_state` without duplicating a single value.

## Where the learner starts

`challenge/work` holds four directories:

1. `mono/`: the configuration to arbitrate. It mixes a platform layer and an
   application, and conditions resources on `terraform.workspace`. A header
   comment states that production is run by another team, with its own rights.
   This directory is read-only, it must not be applied.
2. `socle/` and `app/`: two root configuration skeletons. `socle/main.tf`
   declares `random_pet` and `local_file` resources but its `output` blocks are
   stubbed with `???`. `app/main.tf` is stubbed at the `data` block and at the
   reference to the platform value. Neither is initialised.
3. `bac-a-sable/`: the case where workspaces remain legitimate. A `locals` block
   holds a map indexed by workspace name, with different sizes per environment,
   and the fallback `lookup` is stubbed with `???`.

## The state to reach

1. `socle/` is applied, its local state holds at least one `mode: managed`
   resource, and it exposes two non-empty outputs: the platform identifier and
   the network CIDR.
2. `app/` is applied and its state holds a `mode: data` resource of type
   `terraform_remote_state`, pointing at the state of `socle/`.
3. An output of `app/` matches, exactly, the corresponding output of `socle/`:
   the data crosses two states without being copied.
4. `socle/` and `app/` manage disjoint resource sets: no managed resource address
   appears in both states.
5. Neither `socle/` nor `app/` uses a workspace: no `terraform.tfstate.d`
   directory exists there, the split is by configuration, not by workspace.
6. `bac-a-sable/` has two workspaces named `dev` and `prod`, both applied, each
   with its own state.
7. In `bac-a-sable/`, the size attribute is the `dev` value under the `dev`
   workspace and the `prod` value under `prod`: the map indexed by
   `terraform.workspace` is really wired.
8. All four states are stable: no pending change.

## How it is proven

The tests never open a learner `.tf` file, they query the structured state.

- `terraform show -json` in `socle/` then in `app/`: `values.root_module.resources`
  is walked and filtered on `mode`. Point 1 requires at least one `mode: managed`
  entry in `socle`, point 2 a `mode: data` entry of `type:
  terraform_remote_state` in `app`.
- `terraform output -json` in both: equality between the two proves point 3.
- **The witness that makes point 3 real**: the test replays `socle` with a
  different `cidr`, in a copy, then replays `app` and requires equality again.
  The platform identifier is a `random_pet` keyed on the CIDR, so changing the
  range changes the identifier: a value copied by hand stays frozen and fails.
  Measured during construction: without that `keepers`, changing the CIDR left
  the identifier untouched and the check passed on a hard-coded value.
- The address sets from both `show -json` are intersected: it must be empty
  (point 4).
- Point 5 is checked on disk via the documented internal, `terraform.tfstate.d`.
  It carries a **witness**: the root must first be applied, otherwise the absence
  of a workspace directory would pass on an untouched `challenge/work`.
- For points 6 and 7, the tests query each workspace through `TF_WORKSPACE`,
  which selects it without changing the learner's own selection.
- Point 8 uses `terraform plan -detailed-exitcode` in each configuration, and in
  `bac-a-sable/` for each workspace: exit code 0 expected.

An empty `challenge/work` scores 0 out of 9: with nothing applied, there is no
state to read.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/quand-utiliser-workspaces/
