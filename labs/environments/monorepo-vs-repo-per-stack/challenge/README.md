# Splitting a monorepo into two stacks that talk to each other

## The situation

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

Reference: https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/monorepo-vs-repo-par-stack/ (in French)

## 🎯 Challenge: two stacks that talk to each other

### 📦 Starting point

A monorepo **already split** but **not wired**. Nothing is initialised, no state
exists.

| Path | What it is |
| --- | --- |
| `modules/reseau/` | **complete** local module, leave it alone |
| `stacks/plateforme/` | calls the module, empty `outputs.tf`, one secret declared |
| `stacks/applicatif/` | consumes the platform, **stubbed** `data` block |
| `CIBLE.md` | the state to reach and the three deciding facts |

### ✅ What you must achieve

1. `stacks/plateforme` initialises.
2. Its state holds the module resources, including `random_password.db`.
3. Its root outputs expose `network_name` and `network_cidr`.
4. **No** root output carries the password.
5. `stacks/applicatif` has a `mode: data` entry of type
   `terraform_remote_state`.
6. Its `network_cidr` matches the platform's **exactly**, and the file it
   produces contains it.
7. Both stacks are **idempotent**.

### ⚠️ The heart of the matter

Three measured facts decide the whole exercise.

**A local module does not accept `version`.** `init` fails, and the message says
exactly why. Read it before deleting the line.

**Only ROOT outputs cross.** An output from a nested module stays invisible from
another configuration: whatever must cross the boundary is re-exported
explicitly.

**Publishing an output publishes the whole state.** "any user or server which has
enough access to read the root module output values will also always have access
to the full state snapshot data". The password therefore has no place in a root
output, even marked `sensitive`.

### 🔍 Validation

`dsoxlab check environments-monorepo-vs-repo-per-stack` proves, by execution:

- that the platform tracks both the module **and** its secret;
- that it **re-exports** its two outputs at the root;
- that **none** of its outputs carries the password, compared **value by value**
  rather than on raw text;
- that the application really reads the upstream **state**;
- that the CIDR is **identical** on both sides. It is drawn at random on apply:
  copying it will not hold;
- that both stacks have converged.

Stuck? `dsoxlab hint environments-monorepo-vs-repo-per-stack`.
