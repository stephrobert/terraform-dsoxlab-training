# 🎯 Challenge: the configuration that refuses absurd values

## ✅ Objective

`challenge/work` holds a project whose `variables.tf` and `main.tf` are holed.
`terraform plan` fails as it stands: the `???` are not valid HCL.

Your mission: compute the values with conditional expressions, then **place each
guard at the right level**. The central trap is believing `validation` covers
everything.

## 📋 What is supplied

| File | State |
|---|---|
| `versions.tf` | complete (`required_version = ">= 1.9.0"`) |
| `outputs.tf` | **complete, not to be modified** |
| `variables.tf` | two validations to write |
| `main.tf` | three `locals`, a `content`, a `precondition`, a `postcondition`, a `check` block |

## 🎯 The eight requirements

1. `environment` accepts only `dev`, `staging` or `prod`.
2. `backup_bucket` is refused **empty** when `environment` is `prod`, accepted
   empty otherwise. The condition therefore references **another** variable,
   which Terraform 1.9 allows.
3. `memory_mib` is 512 in `dev`, 2048 in `prod`, and gives way to
   `memory_mib_override` as soon as it is not `null`. `vcpu` is 1, 2 or 4.
4. `second_disk_name` is `null` when the flag is false, which makes the output
   **disappear**, instead of exposing it as `null`.
5. The `precondition` blocks as soon as the memory per vCPU ratio falls below
   **256 MiB**.
6. The `postcondition` reads `self.content` back and requires JSON carrying an
   `env` key.
7. The `check` block **fails in `prod`, and that is intended**: the `apply` must
   succeed in spite of it.
8. A second plan right after the apply proposes nothing.

## 🧩 The heart of it

The four mechanisms are not interchangeable. They differ by **when** they are
evaluated and by **what they block**:

| Mechanism | Can bear on | Effect on failure |
|---|---|---|
| `validation` | an **input variable** only | stops the plan |
| `precondition` | any expression, including a `local` | stops **before** the action |
| `postcondition` | the actual result, through `self` | stops **after** the action |
| `check` block | any expression | **warns only** |

Two direct consequences for this lab:

- Requirement 5 bears on two `locals`. **No `validation` block can carry it**,
  since a validation only lives on an input variable.
- Requirement 7 demands a **non-blocking** mechanism. A `precondition` would
  fail the apply, which would fail the lab.

## 🔍 Validation

```bash
dsoxlab check write-code-conditionals
```

The tests never read your `.tf` files. They run Terraform with various variables
and use only **exit codes** and the **`checks`** array of
`terraform show -json`, whose `kind` field proves which mechanism you actually
wrote.
