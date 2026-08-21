# 🎯 Challenge: a token that never touches the state

## Starting point

`challenge/work` holds a coherent but incomplete project. `versions.tf` and
`variables.tf` are **provided, do not modify them**: `longueur` (number) is 20.
`main.tf` declares an ordinary `random_password.persistant`, a non-secret
`local_file.marqueur`, and a **holed token block** (`???`). `outputs.tf` is
holed. `terraform apply` fails as-is.

## ✅ Objective

1. **`main.tf`, token block**: declare it **`ephemeral`**, so that
   `random_password.jeton` produces a value generated during the operation but
   **never written** to the state.
2. **`outputs.tf`, `jeton_masque`**: expose the ephemeral token's result at the
   root. A root output **rejects** an ephemeral value
   (`Ephemeral value not allowed`): pass it through **`ephemeralasnull()`**,
   which renders it `null`.

Do **not** leak the token: putting it in a persisted attribute (the `local_file`
`content`, for example) would raise `Invalid use of ephemeral value`.

After `apply`, a second `terraform plan` must propose nothing.

## 🧭 What the lab makes you observe

- **An ephemeral value appears nowhere in the state**, unlike
  `random_password.persistant` whose `result` is there in cleartext.
- **A root output rejects an ephemeral**; `ephemeralasnull()` exposes it as
  `null` without disclosing it.
- **An ephemeral in a persisted attribute fails** at plan time.

## 🔍 Validation

```bash
dsoxlab check write-code-sensitive-data-ephemeral-values
```

Four tests reading `terraform show -json` and `output -json`: the single
persisted `random_password` and its cleartext `result`, the total absence of any
ephemeral address in the state, `jeton_masque` at `null`, and idempotence. None
reads your `.tf`.
