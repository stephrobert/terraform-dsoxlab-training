# 🎯 Challenge: constrain and lock versions

## Starting point

`challenge/work` holds `versions.tf` (holed) and `main.tf` (provided, two trivial
resources to pull the `local` and `random` providers). `terraform init` fails
as-is.

## ✅ Objective

Complete the three constraints in `versions.tf`:

1. **`required_version`**: a **literal** constraining Terraform to at least
   `1.15.0` (for example `>= 1.15.0`). The `terraform` block accepts **no**
   variable (`Variables not allowed`).
2. **`local`**: **pin exactly** version `2.5.1` (operator `=`).
3. **`random`**: bound it **pessimistically** to allow the whole compatible
   `3.x` series (from `3.6`) but **never** `4.0` (`~> 3.6`).

After `apply`, a second `terraform plan` must propose nothing.

## 🧭 What the lab makes you observe

- **The exact pin `=`** resolves `local` to exactly `2.5.1`.
- **The pessimistic `~>`** keeps `random` in the `3.x` series.
- **The lock file** records `h1:` hashes and is committed.

## 🔍 Validation

```bash
dsoxlab check write-code-version-constraints
```

Four tests reading `terraform version -json`, the lock file and return codes: the
exact pin of `local`, the pessimistic of `random`, the lock's `h1:` hashes, and
idempotence. None reads your `.tf`.
