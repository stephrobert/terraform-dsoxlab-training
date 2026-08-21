# 🎯 Challenge: expose a secret without disclosing it

## Starting point

`challenge/work` holds a coherent but incomplete project. `versions.tf`,
`variables.tf` and `main.tf` are **provided, do not modify them**: `main.tf`
declares `random_password.admin` and a **non-secret** `local_file.rapport` (it
only writes the length). The variable `longueur_mot_de_passe` (number) defaults
to 24.

`outputs.tf` is **holed** (`???`) on three outputs. `terraform plan` fails as-is.

## ✅ Objective

1. **`mot_de_passe_admin`**: expose `random_password.admin.result`, constrain its
   `type` to `string`, and mark it **`sensitive`**. Without this, the plan is
   rejected ("Output refers to sensitive values").
2. **`resume`**: constrain its `type` to
   `object({ longueur = number, empreinte = string })`, not sensitive. `longueur`
   is `var.longueur_mot_de_passe`; `empreinte` is the `sha256` of the password.
   Since the `sha256` of a secret **stays sensitive**, declassify it with
   **`nonsensitive()`**. **Never** expose the password in cleartext.
3. **`empreinte_rapport`**: the `value` is already written; add a
   **`precondition`** block (with `error_message`) requiring
   `var.longueur_mot_de_passe >= 20`.

After `apply`, a second `terraform plan` must propose nothing.

## 🧭 What the lab makes you observe

- **`sensitive` only hides the secret in human output.** `terraform output
  -json`, `-raw` and the state return it **in cleartext**.
- **Sensitivity propagates**, even through `sha256`: without `nonsensitive()`,
  the fingerprint stays sensitive and `resume` fails or becomes sensitive.
- **An output is not passive**: its `precondition` blocks the plan.

## 🔍 Validation

```bash
dsoxlab check write-code-outputs
```

Eight tests reading `terraform show -json`, `output -json`, `output -raw` and
return codes: the `sensitive` flag, the cleartext value in the output, state and
`-raw`, the `resume` type constraint and absence of secret, the fingerprint, the
`precondition`, and idempotence. None reads your `.tf`.
