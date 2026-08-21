# 🎯 Challenge: four validation levels

## ✅ Objective

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

## 🔍 Validation

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
