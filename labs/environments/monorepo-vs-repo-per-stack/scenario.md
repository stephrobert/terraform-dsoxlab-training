# Scenario: splitting a monorepo into two stacks that talk to each other

**Exam sub-objective covered: 3d (data sharing between configurations), with 3b
(remote state) in support.**

The guide compares monorepo and repo-per-stack on organisational criteria and
leaves aside the technical consequence that trips candidates up: splitting stacks
splits state, and one stack sees nothing of the other until what it must share
has been explicitly published.

## Target capability

Have a downstream stack consume the values produced by an upstream stack through
`terraform_remote_state`, re-exporting at the root the outputs of a nested
module, and refusing to publish sensitive data into a shared state.

## Where the learner starts

`challenge/work` holds a monorepo already split but not wired:

- `modules/reseau/`: a working local module (`random_pet`, `random_integer`,
  `local_file`) exposing `network_name` and `network_cidr`. Do not modify it. The
  CIDR is drawn at random on apply, so no downstream stack can guess it.
- `stacks/plateforme/`: calls the module through a relative path. The block
  carries one extra `version = "???"` line. `outputs.tf` is empty. A
  `random_password "db"` is already declared, with no matching output.
- `stacks/applicatif/`: a stubbed `data "terraform_remote_state" "plateforme"`
  block (`backend = "???"`, `config = { path = "???" }`), a `local_file` whose
  `content` references `???` instead of the upstream outputs, and an `outputs.tf`
  declaring `network_cidr` with a `???` value.
- No state exists, nothing is initialised.

## The state to reach

1. `stacks/plateforme` initialises: no `version` argument next to a local
   `source`, since Terraform refuses that combination.
2. The state of `stacks/plateforme` exists and holds the nested module resources
   in `mode: managed`, including `random_password.db`.
3. The root outputs of `stacks/plateforme` expose `network_name` and
   `network_cidr`, re-exported from the module: a nested module output is not
   readable from another configuration.
4. No root output of `stacks/plateforme` carries the generated password.
5. `stacks/applicatif` holds a `mode: data` entry of type
   `terraform_remote_state` in its state, pointing at the local backend and at
   the upstream state.
6. The `network_cidr` output of `stacks/applicatif` matches the platform's
   exactly, and the file produced by its `local_file` contains that same value.
7. Both stacks are idempotent.

## How it is proven

The tests never open a `.tf` file. They run `terraform show -json` in each stack:
`random_password.db` present in `mode: managed` on the platform side, a
`mode: data` entry of type `terraform_remote_state` on the application side. They
run `terraform output -json` in both stacks and compare values: `network_cidr`
must be identical on both sides, which a learner can only obtain by really wiring
the data source, since the value is drawn at random on apply. Finally,
`terraform plan -detailed-exitcode` must return 0 in both stacks.

**On the secret check, one precaution learned the hard way.** The comparison is
made on **decoded** values, never on the raw JSON text: a password generated with
`special = true` contains characters that JSON escapes (`"` becomes `\"`), so a
substring search over the raw output fails to find it and lets a published secret
through. The first version of the test did exactly that, and its counter-test
passed 7/7 while the secret was in fact exposed.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/monorepo-vs-repo-par-stack/
