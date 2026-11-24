# What expressions really compute

## The situation

**Exam objective: 2e (declaring and consuming expressions, types and values).**

Writing an interpolation fails no one. What fails are the fine rules: a managed resource is referenced with no prefix, the `==` operator does not convert types where arithmetic does, precedence puts `*` before `+`, and `null` omits an argument where an empty string would be an invalid value. The learner must write these expressions and prove it, with evidence.

## Target capability

Read and write correct Terraform expressions: reference a managed resource with no prefix, anticipate the result of an equality between different types, apply operator precedence, and use `null` to make an argument optional. Know how to check the **type** of a result, not just its value.

## Where the learner starts

`challenge/work/` holds an incomplete project. No VM, no remote account: only `hashicorp/random` and `hashicorp/local` are used, `terraform init` is already run. The lab runs anywhere `terraform` is on the PATH, offline.

The directory has `versions.tf`, `variables.tf` (`seuil`, number, default 3; `perm_forcee`, string, default `""`), a `main.tf` where `random_pet.hote` is declared, `local_file.marqueur` references its id in its filename, and its `file_permission` is a `???`, and a holed `outputs.tf`:

```hcl
output "ref_hote"        { value = ??? }   # resource id, WITH NO prefix
output "egalite_stricte" { value = ??? }   # var.seuil == "3" (== does not convert)
output "calcul"          { value = ??? }   # 1 + twice var.seuil (precedence)
output "perm_effective"  { value = ??? }   # the permission actually applied
```

`terraform apply` fails as-is: the `???` are not valid HCL, and a `file_permission` set to `""` would be rejected anyway.

## The state to reach

1. `file_permission` is `null` when `perm_forcee` is empty (so the argument is omitted), and the given value otherwise. Writing `""` directly fails: an empty string is not an omission.
2. `ref_hote` exposes the id of `random_pet.hote`, referenced **with no prefix**.
3. `egalite_stricte` is **false**: `var.seuil` (number 3) is not equal to the string `"3"`, because `==` does not convert.
4. `calcul` is **7**: `1 + var.seuil * 2`, multiplication first.
5. `perm_effective` is `0777` on a default apply: the omitted permission falls back to the provider default.
6. The project converges: a second plan right after apply proposes nothing.

## How it is proven

The tests never open the learner's `.tf` files and parse no human output. They drive Terraform in `challenge/work` and read only JSON or return codes.

1. `terraform show -json` gives the `random_pet` id, and `terraform output -json` gives `ref_hote`: the two are equal.
2. `egalite_stricte` is `false` in `output -json`.
3. `calcul` is `7` and is a number.
4. `perm_effective` is `0777` by default; a replay with `-var perm_forcee=0600` makes it `0600`, then the state is restored.
5. `terraform plan -detailed-exitcode` returns 0 right after apply.

Reference: https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/expressions-terraform/ (in French)

## 🎯 Challenge: write expressions that compute correctly

### Starting point

`challenge/work` holds a coherent but incomplete project. `versions.tf` and
`variables.tf` are **provided, do not modify them**: `seuil` (number) is 3,
`perm_forcee` (string) defaults to `""`. `main.tf` declares `random_pet.hote`
and `local_file.marqueur`, but the latter's `file_permission` is a `???`.
`outputs.tf` is holed on four outputs. `terraform apply` fails as-is.

### ✅ Objective

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

### 🧭 What the lab makes you observe

- **A managed resource is referenced with no prefix.**
- **`==` does not convert**: the number 3 is not equal to `"3"` (result
  `false`), whereas arithmetic does convert.
- **`*` comes before `+`**: `1 + var.seuil * 2` is 7.
- **`null` omits an argument**: `perm_effective` falls back to `0777`, the
  provider default, where `""` would have failed.

### 🔍 Validation

```bash
dsoxlab check write-code-expressions
```

Six tests reading `terraform show -json`, `output -json` and return codes: the
prefix-less reference, the non-converting equality, precedence (and the number
type), the `null` omission (default 0777, then a forced permission), and
idempotence. None reads your `.tf`.
