# Scenario: split a monolith without moving the plan

**Exam sub-objective covered: 2e (declare and consume variables and outputs, including value precedence), leaning on 2a (validate the configuration).**

Terraform evaluates every `.tf` file in a directory as a single document: file
names and their order have no functional effect. Splitting a monolith must
therefore produce exactly the same plan, and that is what gets proven, not the
presence of well-named files.

## Target capability

Reorganise an existing configuration into thematic files and show, by comparing
two JSON plans, that the resolved configuration stayed strictly identical. Then
know which source of value wins when several define the same variable, and that
declaring the same name twice breaks the module.

## Where the learner starts

`challenge/work` holds a single `tout.tf` file that piles up, out of order:

- the `terraform` block with `required_version` and `required_providers` for
  `local`, `null` and `random`;
- the matching `provider` blocks;
- four `variable` blocks, three of them with a `default`;
- a `locals` block;
- a `random_pet`, a `null_resource` and a `local_file` writing a report into the
  working directory;
- three `output` blocks exposing the effective value of the variables.

No values file, no state, no saved plan. The three providers only write in the
current directory: no VM, no credential, no remote infrastructure.

## The state to reach

1. A reference plan is frozen **before** any reorganisation, produced by
   `terraform plan -out` then `terraform show -json`.
2. `tout.tf` is gone, replaced by `terraform.tf`, `providers.tf`,
   `variables.tf`, `locals.tf`, `main.tf` and `outputs.tf`. No block is added,
   removed or modified: only their location changes.
3. Every variable, local and output name is declared **exactly once** across the
   directory. `terraform validate` exits successfully.
4. A plan regenerated after the split, with the same input values, is identical
   to the reference plan.
5. A `terraform.tfvars` sets two variables, and an `env.auto.tfvars` redefines
   one of the two: the `auto` file value is the one retained.
6. A `TF_VAR_` environment variable targets a variable also present in
   `terraform.tfvars`: the file value wins, which materialises the real rank of
   `TF_VAR_`, just above the `default`.
7. The fourth variable, with neither `default` nor file value, is provided only
   by `-var` on the command line and wins over every other source.
8. The configuration is applied, then a second plan proposes no change.

## How it is proven

The tests only read structured state. No assertion bears on Terraform's
human-facing output, and none merely observes that a file carries the right
name.

- **Plan invariance**: the `resource_changes` lists of both JSON plans are
  compared address by address, action by action, and on `change.after` values,
  after neutralising volatile fields. Any divergence fails the lab.
- **Real split**: measured on 2026-09-23, a plan's JSON carries **no** file name,
  neither in `configuration` nor anywhere else. The proof therefore goes through
  `terraform validate -json`, whose diagnostics name the file of the conflicting
  declaration. The test drops a probe redeclaring a block, and reads the file it
  points at. The probe's name matters: `.tf` files are read in alphabetical
  order and it is the **second** declaration encountered that gets reported. A
  probe named `aaa-sonde.tf` is read first, so the diagnostic designates the
  original; a probe named `zzz-sonde.tf` would designate itself and prove
  nothing. Both cases were measured, across the six block families. The proof
  thus bears on the resolved configuration, never on an `ls`.
- **No duplicates**: the same mechanism establishes it. Every probe is removed
  whatever happens, and a separate check confirms `terraform validate` returns
  to green.
- **Value precedence**: after `terraform apply`, `terraform output -json`
  exposes the effective value of each variable. The test checks the expected
  value for each source, including the case where `TF_VAR_` is overridden by
  `terraform.tfvars`, then replays a variant with `-var` and compares again.
- **Convergence**: `terraform plan -detailed-exitcode` must return **0**. A code
  2 signals a non-empty plan and fails the lab.
