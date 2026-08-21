# 🎯 Challenge: iterate without leaking

## Starting point

`challenge/work` holds `versions.tf`, `variables.tf` (`services`, a NON-sensitive
set; `db_password`, sensitive), `main.tf` (`local_file.conf`'s `for_each` is
holed), and `outputs.tf` (holed). `terraform apply` fails as-is.

## ✅ Objective

1. **`main.tf`, `for_each`**: iterate over **`var.services`** (non-sensitive). A
   **sensitive** value as a `for_each` key is rejected (`Invalid for_each
   argument`). The `content` injects `var.db_password` (do not modify) and
   contaminates the attribute.
2. **`outputs.tf`, `empreinte`**: expose the password's **`sha256`** **without**
   disclosing it or making the output sensitive. The `sha256` of a secret stays
   sensitive: **declassify** it with `nonsensitive()`.

After `apply`, a second `terraform plan` must propose nothing.

## 🧭 What the lab makes you observe

- **A sensitive value cannot be a `for_each` key**: marking `sensitive` can break
  a `for_each`.
- **Contamination is read in `sensitive_values`** (`content` at `true`).
- **`nonsensitive()`** publishes a hash without disarming the secret.

## 🔍 Validation

```bash
dsoxlab check write-code-sensitive-data-sensitive-values
```

Four tests reading `terraform show -json` and `output -json`: the non-sensitive
`for_each` keys, the `content` contamination, the declassified fingerprint, and
idempotence. None reads your `.tf`.
