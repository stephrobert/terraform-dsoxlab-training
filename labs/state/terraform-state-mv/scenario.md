# Scenario: refactor without destroying, from `state mv` to the `moved` block

**Target exam objective: 1e.**

Renaming a block or pushing it into a module amounts, by default, to a destroy
followed by a create: the object changes identity. This lab tackles the trap the
official documentation flags and the guides keep quiet about: reconciling the
state by hand works, but leaves no replayable trace for the team, whereas a
versioned `moved` block does the same thing while being read, reviewed and
replayed by everyone.

## Target capability

Reattach already created objects to new addresses without recreating them: with
`terraform state mv` when the state has drifted from the code, with a `moved`
block when the refactoring starts from the code, proving in both cases that the
existing values survived.

## Where the learner starts

`challenge/work` holds a configuration already applied by "the previous team",
whose code was refactored without anyone touching the state:

- `main.tf`: the `terraform` block (`required_version = ">= 1.1"`, provider
  `hashicorp/random ~> 3.6`), the `random_pet.frontend` and
  `random_integer.frontend_port` resources, and a `module "secret"` call to
  `./modules/secret`.
- `modules/secret/main.tf`: `random_string.this` and its output.
- `terraform.tfstate`: three very real objects, but at the **old** addresses
  `random_pet.web`, `random_integer.web_port` and `random_string.db_secret`.
- `moved.tf`: a punched-out skeleton, a single block, `from = ???` and `to = ???`.
- `reference/etat-initial.tfstate`: a frozen copy of the starting state, read by
  the tests as the reference for the values. Never to be modified.
- No `.terraform`: the `terraform init` is the learner's job.

The first `terraform plan` announces 3 resources to create and 3 to destroy.

Two methods are imposed: both renames are settled imperatively with
`terraform state mv` (the code is already written, only the state lags), and the
move into the module is settled declaratively with the `moved` block, then
applied.

## Target state

1. The state objects are at exactly the addresses `random_pet.frontend`,
   `random_integer.frontend_port` and `module.secret.random_string.this`; none of
   the three old addresses remains.
2. The recorded values are those of `reference/etat-initial.tfstate`: nothing was
   recreated along the way.
3. `terraform plan -detailed-exitcode` exits 0: code and state converge.
4. The move into the module was made **declaratively**, which the plan JSON proves
   through `previous_address`.
5. The `moved` block is still in the code after the apply: removing it is a
   breaking change, and the official documentation recommends retaining the
   history of moves.

## How it is proven

- `terraform show -json` lists the `mode: managed` objects of the root module and
  of the child modules: the tests compare the whole address set with the expected
  one and check the old addresses are gone.
- The values from that JSON are confronted with `reference/etat-initial.tfstate`.
  A single divergence signals a recreation: `random_pet`, `random_integer` and
  `random_string` draw fresh values on every creation.
- `terraform plan -detailed-exitcode` must return 0; code 2 signals pending
  changes, hence an incomplete reconciliation.
- The declarative step is proven by a **replay**, because the move is already
  applied in the final state: the tests copy `challenge/work` into a temporary
  directory, bring the object back to its old address with
  `terraform state mv module.secret.random_string.this random_string.db_secret`,
  then record a new plan. Its JSON must contain a `resource_changes[]` whose
  `address` is `module.secret.random_string.this`, whose `previous_address` is
  `random_string.db_secret` and whose `change.actions` is `["no-op"]`. Terraform
  only writes `previous_address` when a `moved` block was taken into account:
  `state mv` never produces it. That is the discriminant between the two methods,
  and it forbids validating the declarative step with an imperative shortcut.
- Negative check, in another copy: with the `moved` block removed, the same plan
  goes back to `delete` plus `create`. That is exactly the "breaking change" the
  documentation describes.
- The two imperative renames deliberately have no `moved` block: their only proof
  is the presence of the original values at the new addresses, which a destroy
  plus create cannot fake.
- No test ever reads the content of the learner's `.tf` files.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-mv/
