# 🎯 Challenge: one end-of-life batch, four different decisions

## 📦 Starting point

`challenge/work` holds a complete project that was **never applied**. Bringing it
up is on you:

```bash
terraform init
terraform apply
```

Eight addresses then enter the state, and seven files appear on disk:

| Address | File | What it must become |
| --- | --- | --- |
| `random_pet.jeton` | (none) | stays managed, start to finish |
| `local_file.rapports["mensuel"]` and `["annuel"]` | `rapport-*.txt` | **bequeathed**: out of state, files kept |
| `local_file.bacs["beta"]` | `bac-beta.txt` | **bequeathed**, alone among the three bins |
| `local_file.bacs["alpha"]` and `["gamma"]` | `bac-*.txt` | stay managed |
| `local_file.cache` | `cache.txt` | **destroyed**, file included |
| `local_file.journaux` | `journaux.txt` | migration **written but not applied** |

Two files, two statuses: `main.tf` is complete and **meant to be edited**
(removing a `resource` block, removing a key from a `for_each`), `migration.tf`
carries two `removed` blocks **shipped commented out** and holed with `???`. A
third block must be written from scratch.

**The note left in `migration.tf` is false.** It claims a `removed` block merely
takes a resource out of the state and that `destroy = true` would be needed to
destroy. Do not trust it: read the plan.

## ✅ Objective

Carry out this batch migration, deciding resource by resource whether the real
object survives or disappears, and using the right way for each grain.

## 📋 What you must obtain

1. The state carries only **four addresses**: `random_pet.jeton`,
   `local_file.bacs["alpha"]`, `local_file.bacs["gamma"]` and
   `local_file.journaux`.
2. The **six bequeathed files** still exist, with the content written during the
   first `apply`: both reports, the three bins and the journal.
3. `cache.txt` is **gone** from disk, and its address from the state.
4. Only the `beta` key left `local_file.bacs`, and it **no longer appears in the
   `for_each`**: without that alignment, Terraform recreates the instance and
   overwrites the bequeathed file.
5. The migration of `local_file.journaux` is **prepared, not applied**: its
   `resource` block is gone, its `removed` block is written, and
   `terraform plan -detailed-exitcode` exits with **code 2** carrying a single
   change, `forget` on that address.

## ⚠️ The heart of the matter

Two boundaries decide everything, and neither can be guessed:

| What you want | What to write |
| --- | --- |
| Bequeath an object (it survives) | `removed` + `lifecycle { destroy = false }` |
| Delete an object | `removed` alone, or `destroy = true` |
| Take out **a single instance** of a `for_each` | `terraform state rm`, then drop the key from the `for_each` |

The `removed` block refuses an instance key in its `from`
(`Resource instance keys not allowed`), and it **destroys by default**. A mistake
there cannot be undone: the file is deleted, and the tests will see it.

## 🔍 Validation

`dsoxlab check state-removed-block` proves, by execution:

- the state carries **exactly** the four expected addresses;
- the six bequeathed files exist and still carry the **token read from the
  state**: a recreated file would hold different content;
- `cache.txt` is indeed absent, from disk and from state;
- no pending change on the bins, which proves the `for_each` alignment;
- exactly one pending change, `forget` on `local_file.journaux`, and
  `plan -detailed-exitcode` at **code 2**;
- two behaviour checks played in a temporary copy, never touching your work.

No test opens your `.tf` files: they read the state, the disk and saved plans.

Stuck? `dsoxlab hint state-removed-block`.
