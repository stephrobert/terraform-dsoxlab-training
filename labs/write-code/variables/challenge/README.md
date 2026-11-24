# Terraform variables, typing, validation and precedence

## The situation

**Exam objective: 2e (variables and outputs, complex types), with a spillover to 2f (sensitive data).**

Declaring a variable and setting a `default` fails no one. This lab covers the three traps that do fail people: the real precedence order of value sources, the explicit `null` that overwrites a `default` until `nullable = false` is set, and the confusion between `sensitive` (a display mask) and a value that stays in cleartext in the state file.

## Target capability

Parameterize a configuration so it produces the right result whatever value source is used: constrain a complex type, reject an invalid value before any provider call, guarantee a `null` falls back to the default, and know which source wins when several disagree.

## Where the learner starts

`challenge/work` holds an incomplete but coherent configuration:

- `versions.tf` and `main.tf`: provided, not modifiable. `main.tf` builds a `local_file` rendered from the variables, a `random_password`, and the `output` blocks that expose everything. Its shape dictates the expected types.
- `variables.tf`: holed. The blocks exist, but `type`, `validation`, `nullable` and `sensitive` are replaced by `???`, on `env`, `nodes` (a map of objects with optional attributes), `retention_days` and `db_password`.
- `terraform.tfvars`: provided, not modifiable, sets `env = "dev"` and, deliberately, `retention_days = null`.
- `zz-override.auto.tfvars`: provided, not modifiable, resets `env`.

`terraform init` is already run. As-is, `terraform validate` fails.

## The state to reach

1. `terraform validate` succeeds and `terraform apply` completes with no intervention.
2. `nodes` is constrained to `map(object(...))` with at least one `optional()` attribute carrying a default: the incomplete entry in the value file is filled in by Terraform itself.
3. A value outside the allowed set for `env` fails the `plan` on the `validation` block's message, without calling any provider.
4. `retention_days` holds its default in the final state even though the value file assigns it `null`: `nullable = false` guarantees this.
5. `env` holds what `zz-override.auto.tfvars` sets, even when a contradictory `TF_VAR_env` is exported, and yields to a `-var`.
6. `db_password` is sensitive: the matching output is flagged as such.

## How it is proven

The tests never open the learner's `.tf` files.

- `terraform validate -json` must return `valid: true`.
- `terraform output -json` covers states 2, 4 and 6: full structure of `nodes` after the `optional()` defaults, value of `retention_days` compared to the expected default, `sensitive: true` flag on the password.
- `terraform show -json` reads back the content written by the `local_file` resource in `mode: managed`: the values traversed the configuration, not only the outputs. The password output value also appears in cleartext, proving `sensitive` is a display mask, not a state protection.
- State 3 is proven by exit code: `plan` with a forbidden value in `-var` must fail, the same plan with an allowed value must pass.
- State 5 is proven by exit codes on `plan -detailed-exitcode`: with `TF_VAR_env` exported to another value, the plan stays stable (auto.tfvars wins); with `-var`, it proposes a change.
- `terraform plan -detailed-exitcode` must return 0 after the final apply.

Reference: https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/variables-terraform/ (in French)

## 🎯 Challenge: type, validate, and master precedence

### Starting point

`challenge/work` holds a coherent but incomplete configuration. `versions.tf`
and `main.tf` are **provided, do not modify them**: `main.tf` consumes the
variables (a rendered `local_file`, a `random_password`, the outputs), and its
shape **dictates the expected types**.

Two value files are provided, **do not modify them**:

- `terraform.tfvars`: sets `env = "dev"` and, deliberately, `retention_days = null`.
- `zz-override.auto.tfvars`: resets `env = "staging"`.

`variables.tf` is **holed** (`???`) on four variables: `env`, `nodes`,
`retention_days` and `db_password`. `terraform validate` fails as-is.

### ✅ Objective

Complete the four variables:

1. **`env`** (string): add a **`validation`** that rejects any value outside
   `dev`, `staging`, `prod`, failing at plan time before any provider.
2. **`nodes`**: constrain the **type** to `map(object(...))` with `size`
   (string), `replicas` (number, **optional**, default 1) and `public` (bool,
   **optional**, default false). The incomplete entry in the value file must be
   filled in by Terraform.
3. **`retention_days`** (number, default 7): guarantee an explicit `null` **falls
   back to the default** with **`nullable = false`**.
4. **`db_password`** (string): mark it **`sensitive`**.

After `apply`, a second `terraform plan` must propose nothing.

### 🧭 What the lab makes you observe

- **`env` is `staging`**, not `dev`: a `*.auto.tfvars` beats `terraform.tfvars`.
  An exported `TF_VAR_env` does not dislodge it; only a `-var` does.
- **`retention_days` is 7** despite the file's `null`: `nullable = false`
  guarantees it.
- **`db_password` stays in cleartext in the state.** `sensitive` masks display,
  but `terraform show -json` returns the value. It is not a secret protection.

### 🔍 Validation

```bash
dsoxlab check write-code-variables
```

Eight tests reading `terraform validate -json`, `show -json`, `output -json` and
return codes: validity, the filled `optional()` defaults, `nullable`, the
`sensitive` mask against the cleartext state, source precedence, validation
rejection, and idempotence. None reads your `.tf`.
