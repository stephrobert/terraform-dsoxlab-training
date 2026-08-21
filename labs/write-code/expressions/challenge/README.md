# 🎯 Challenge: write expressions that compute correctly

## Starting point

`challenge/work` holds a coherent but incomplete project. `versions.tf` and
`variables.tf` are **provided, do not modify them**: `seuil` (number) is 3,
`perm_forcee` (string) defaults to `""`. `main.tf` declares `random_pet.hote`
and `local_file.marqueur`, but the latter's `file_permission` is a `???`.
`outputs.tf` is holed on four outputs. `terraform apply` fails as-is.

## ✅ Objective

1. **`main.tf`, `file_permission`**: make the permission optional. When
   `perm_forcee` is `""`, the argument must be **omitted**, which is expressed
   with **`null`**, not an empty string (which would be an invalid permission).
2. **`ref_hote`**: expose the id of `random_pet.hote`. A managed resource is
   referenced **with no prefix** (`random_pet.hote.id`, never `resource....`).
3. **`egalite_stricte`**: is `var.seuil` equal to the **string** `"3"`? The `==`
   operator **does not convert** types.
4. **`calcul`**: `1` plus twice `var.seuil`, in one expression. **Precedence**
   puts `*` before `+`.
5. **`perm_effective`**: the permission actually applied to
   `local_file.marqueur`.

After `apply`, a second `terraform plan` must propose nothing.

## 🧭 What the lab makes you observe

- **A managed resource is referenced with no prefix.**
- **`==` does not convert**: the number 3 is not equal to `"3"` (result
  `false`), whereas arithmetic does convert.
- **`*` comes before `+`**: `1 + var.seuil * 2` is 7.
- **`null` omits an argument**: `perm_effective` falls back to `0777`, the
  provider default, where `""` would have failed.

## 🔍 Validation

```bash
dsoxlab check write-code-expressions
```

Six tests reading `terraform show -json`, `output -json` and return codes: the
prefix-less reference, the non-converting equality, precedence (and the number
type), the `null` omission (default 0777, then a forced permission), and
idempotence. None reads your `.tf`.
