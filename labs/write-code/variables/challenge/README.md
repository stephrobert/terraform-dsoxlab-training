# 🎯 Challenge: type, validate, and master precedence

## Starting point

`challenge/work` holds a coherent but incomplete configuration. `versions.tf`
and `main.tf` are **provided, do not modify them**: `main.tf` consumes the
variables (a rendered `local_file`, a `random_password`, the outputs), and its
shape **dictates the expected types**.

Two value files are provided, **do not modify them**:

- `terraform.tfvars`: sets `env = "dev"` and, deliberately, `retention_days = null`.
- `zz-override.auto.tfvars`: resets `env = "staging"`.

`variables.tf` is **holed** (`???`) on four variables: `env`, `nodes`,
`retention_days` and `db_password`. `terraform validate` fails as-is.

## ✅ Objective

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

## 🧭 What the lab makes you observe

- **`env` is `staging`**, not `dev`: a `*.auto.tfvars` beats `terraform.tfvars`.
  An exported `TF_VAR_env` does not dislodge it; only a `-var` does.
- **`retention_days` is 7** despite the file's `null`: `nullable = false`
  guarantees it.
- **`db_password` stays in cleartext in the state.** `sensitive` masks display,
  but `terraform show -json` returns the value. It is not a secret protection.

## 🔍 Validation

```bash
dsoxlab check write-code-variables
```

Eight tests reading `terraform validate -json`, `show -json`, `output -json` and
return codes: validity, the filled `optional()` defaults, `nullable`, the
`sensitive` mask against the cleartext state, source precedence, validation
rejection, and idempotence. None reads your `.tf`.
