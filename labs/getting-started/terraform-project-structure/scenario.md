# Scenario: split a monolith without moving the plan

**Exam objective targeted: 2e (declare and consume variables and outputs, including value precedence), with 2a (validate the configuration) in support.**

Terraform evaluates every `.tf` file in a directory as a single document: file names and
their order have no functional effect. Splitting a monolith must therefore produce exactly
the same plan, and that is what gets proven, not the presence of well-named files.

## Capability targeted

Reorganise an existing configuration into thematic files and demonstrate, by comparing two
JSON plans, that the resolved configuration stayed strictly identical. Then know which
value source prevails when several define the same variable, and that declaring the same
name twice breaks the module.

## Where the learner starts

`challenge/work` holds a single `tout.tf` file piling up, out of order: the `terraform`
block with `required_version` and `required_providers` for `local`, `null` and `random`;
the matching `provider` blocks; four `variable` blocks, three of them with a `default`; a
`locals` block; a `random_pet`, a `null_resource` and a `local_file` writing a report into
the working directory; and four `output` blocks exposing the effective value of the
variables.

It also holds `reference/monolithe.tf.txt`, a reference copy supplied and not modifiable,
whose extension is not `.tf` so Terraform does not load it. The tests use it to rebuild the
original plan rather than trusting one the learner froze.

No values file, no state, no saved plan. The three providers only write into the current
directory: no VM, no credential, no remote infrastructure.

## The state to reach

1. `tout.tf` is gone, replaced by `terraform.tf`, `providers.tf`, `variables.tf`,
   `locals.tf`, `main.tf` and `outputs.tf`. No block is added, removed or modified: only
   their location changes.
2. Every variable, local and output name is declared exactly once across the directory.
   `terraform validate` succeeds.
3. A plan regenerated after the split, with the same input values, is identical to the
   plan the monolith produced.
4. A `terraform.tfvars` fixes two variables, and an `env.auto.tfvars` redefines one of the
   two: the `auto` file's value is the one retained.
5. A `TF_VAR_` environment variable targets a variable also present in `terraform.tfvars`:
   the file's value prevails, which shows the real rank of `TF_VAR_`, just above the
   `default`.
6. The fourth variable, with neither `default` nor value in a file, is supplied only
   through `-var` on the command line and prevails over every other source.
7. The configuration is applied, then a second plan proposes no change.

## How it is proven

The tests read only structured output. No assertion is made on Terraform's human output,
and none settles for observing that a file carries the right name.

- **Plan invariance**: the `resource_changes` lists of both JSON plans are compared address
  by address, action by action, and on `change.after` values, after neutralising volatile
  fields. Any divergence fails the lab. Both plans are produced from a state-free copy, so
  that the order of the tests cannot make one announce `no-op` and the other `create`.
- **Real split, proven by ablation**: measured on 2026-09-24, `terraform show -json`
  exposes no source position whatsoever, so nothing says which file a block comes from.
  Each expected file is therefore removed in a copy, and something must break: without
  `variables.tf` and `locals.tf`, `validate` refuses; without `main.tf`, the plan carries
  no resource; without `outputs.tf`, it carries no output change.
- **No duplicate names**: the test drops an extra `.tf` redeclaring an existing variable,
  checks that `terraform validate -json` returns a diagnostic of severity `error`, then
  removes the file and confirms the return to green.
- **Value precedence**: after `terraform apply`, `terraform output -json` exposes each
  variable's effective value, including the case where `TF_VAR_` is beaten by
  `terraform.tfvars`.
- **Convergence**: `terraform plan -detailed-exitcode` must return 0.

Three of these tests carry a guard refusing to measure while the monolith is still in
place: without it they were green before any work, since the monolith already produces a
plan identical to itself, already validates, and already refuses a duplicate.
