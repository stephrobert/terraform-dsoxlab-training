# Four validation levels, only one that does not block

## The situation

**Target exam objective: 2a, use the language features to validate a configuration.**

Terraform offers four validation mechanisms that look alike on paper and behave differently at runtime. This lab makes them coexist to show which one stops the operation and which only warns.

## Target capability

Place a constraint at the right level for the intended effect: reject an input before the plan (`validation` in a variable, including a cross-validation that references another variable), reject an assumption before creation (`precondition` in `lifecycle`), reject a result after creation (`postcondition`, the only one with `self`), or watch without blocking (a `check` block). Then read the verdict of all four in a single machine call, the `checks` array of `terraform show -json`.

## Where the learner starts

`challenge/work` holds an incomplete configuration: `random` and `local` providers only, no VM, no cloud. `versions.tf` is provided and complete (`required_version >= 1.15.0`).

- `variables.tf`: `nom_projet`, `taille_lot` and `taille_max` declared, their `validation` blocks present but `condition` and `error_message` are `???`. The `taille_lot` validation is about `taille_max`: it references another variable.
- `main.tf`: a `random_pet` with `count = var.taille_lot` and a `local_file` writing a manifest (one name per line). The `lifecycle` block has a holed `precondition` and `postcondition`, with comments on what each guarantees.
- `outputs.tf`: a `noms` output whose `precondition` block has a hole.
- `checks.tf`: a `check` block with a scoped data source re-reading the manifest, and a holed `assert` that the brief asks to fail on the final state.

## The target state

1. The configuration applies and converges, **despite** the failing `check` block: `random_pet` and `local_file` are in the state as `mode: managed`, the manifest has as many lines as `taille_lot`. Apply returns 0.
2. The top-level `checks` array of `show -json` carries the **four** `address.kind`: `var`, `resource`, `output_value` and `check`.
3. The first three are `status: pass`, the `check` block is `status: fail` and carries the learner's message in `instances[].problems[].message`.
4. A `precondition` blocks a plan: `plan -var taille_max=20` fails (the `taille_max <= 10` guard is violated, and instances exist).
5. `terraform validate -json` returns `valid: true` on a value that violates the cross-validation, while the matching plan (`plan -var taille_lot=10`) fails: the so-called validate command declares valid what the plan refuses.
6. `plan -detailed-exitcode` returns **2** on the converged configuration, while the plan announces zero add, change and destroy. The only non-`no-op` entry of `resource_changes` is the data source scoped in the `check` block, with action `read`: it is re-read on every plan by construction.

## How it is proven

The tests never open a learner `.tf` file and never read human output. They run Terraform in `challenge/work` and work on JSON and return codes.

1. `terraform show -json`: the `checks` array counts distinct `address.kind`, requires the four, checks the `status` (three `pass`, one `fail`), and that the failing `check` carries a non-empty `error_message`.
2. `terraform plan -var taille_max=20`: non-zero return code, with "Resource precondition failed".
3. `terraform validate -json` returns `valid: true`; `terraform plan -var taille_lot=10` fails. The test compares the two.
4. `terraform plan -detailed-exitcode` returns 2; the plan re-read as JSON has a single non-`no-op` entry, the `check` data source, as `read`.

A continuous-integration pipeline that decided on that return code would always believe changes remain.

Reference: https://developer.hashicorp.com/terraform/language/expressions/custom-conditions

## 🎯 Challenge: four validation levels

### ✅ Objective

In `challenge/work`, fill the **four levels** of validation. Four files have holes
(`condition` and `error_message` to write):

1. **`variables.tf`**: the `validation` of `nom_projet` (1 to 20 characters) and
   the one of `taille_lot` (**cross**-validation: `taille_lot <= taille_max`).
2. **`main.tf`**: in `lifecycle`, the `precondition` (guard: `taille_max <= 10`)
   and the `postcondition` (the generated name is not empty; it is the only one
   with `self`).
3. **`outputs.tf`**: the `precondition` of the `noms` output (as many names as
   `taille_lot`).
4. **`checks.tf`**: the `assert` of the `check` block. It must **fail** on the
   final state (the manifest has `taille_lot` lines, not `taille_max`): that is
   how you show a `check` **warns without blocking**.

### 🔍 Validation

`dsoxlab check write-code-validation-check-preconditions` proves, on JSON:

- the `checks` array of `show -json` carries the **four** `kind` (`var`,
  `resource`, `output_value`, `check`); the first three `pass`, the `check`
  `fail` with your message;
- apply succeeds **despite** that failing `check`;
- `plan -var taille_max=20` fails (precondition);
- `validate -json` returns `valid: true` where `plan -var taille_lot=10` fails;
- `plan -detailed-exitcode` returns `2` (the `check` data source is re-read on
  every plan).

Stuck? `dsoxlab hint write-code-validation-check-preconditions`.
