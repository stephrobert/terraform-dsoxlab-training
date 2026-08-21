# 🎯 Challenge: two resources to stop managing, no file to lose

## 📦 Starting point

`challenge/work` holds a complete project that was **never applied**. Bringing it
up is on you:

```bash
terraform init
terraform apply
```

Four resources then enter the state, and three files appear on disk:

| Address | File | Role |
| --- | --- | --- |
| `local_file.rapport` | `rapport.txt` | to remove the **imperative** way |
| `local_file.archive` | `archive.txt` | to remove the **declarative** way |
| `local_file.conserve` | `conserve.txt` | witness, stays managed |
| `random_pet.identifiant` | (none) | witness, stays managed |

Two files, two statuses: `main.tf` is complete and **meant to be edited**
(removing a `resource` block is part of the exercise), `retrait.tf` carries a
`removed` block **shipped commented out** and holed by two `???`. Being commented
is what lets the first `apply` go through: uncomment it when you need it.

## ✅ Objective

Stop managing `local_file.rapport` and `local_file.archive` without either file
leaving the disk, using **a different way for each**.

## 📋 What you must obtain

1. The state carries **only** the two witnesses, `local_file.conserve` and
   `random_pet.identifiant`, both in `mode: managed`.
2. `local_file.rapport` left the state through `terraform state rm`, and its
   `resource` block is gone from `main.tf`: while it stays there, the resource is
   an **orphan** and the next plan wants to recreate it.
3. `local_file.archive` left the state through the `removed` block in
   `retrait.tf`, completed then **applied**. Its `resource` block is gone from
   `main.tf` too: the two cannot coexist.
4. `rapport.txt` and `archive.txt` are still on disk, with their original content
   (`rapport-origine` and `archive-origine`).
5. `terraform plan -detailed-exitcode` exits with **code 0**: nothing pending.

## ⚠️ The heart of the matter

A `removed` block **destroys by default**. Neither the `lifecycle` block nor the
`destroy` argument is mandatory, and Terraform gives you no warning:

| Spelling | Planned action | The real object |
| --- | --- | --- |
| `removed` without a `lifecycle` block | `delete` | **destroyed** |
| `removed` with `lifecycle { destroy = true }` | `delete` | **destroyed** |
| `removed` with `lifecycle { destroy = false }` | `forget` | kept |

A mistake here cannot be undone: the file is deleted, and the test reading its
content will see it. Check your plan **before** applying it.

## 🔍 Validation

`dsoxlab check state-terraform-state-rm` proves, by execution:

- the state carries **exactly** the two witnesses, through `terraform show -json`;
- `rapport.txt` and `archive.txt` exist, with their original content: the only
  outcome telling a removal from a destruction;
- `plan -detailed-exitcode` returns **0**, so neither an orphan nor a forgotten
  `removed` block;
- two behaviour checks, played in a temporary copy and never touching your work:
  a resource removed from the state but still declared is planned as `create`,
  and a `removed` block deprived of `destroy = false` is planned as `delete`.

No test opens your `.tf` files: they read the state, the disk and saved plans.

Stuck? `dsoxlab hint state-terraform-state-rm`.
