# Bequeath an infrastructure without destroying it, with the removed block

## The situation

**Target exam sub-objectives: 1e (manage state) and 4c (refactor a configuration).**

This lab tackles the costliest misreading of the `removed` block: believing it
merely takes a resource out of the state, and that `destroy = true` would be the
option to add to go further. It is the other way around. Destroying is the
**default** behaviour; `destroy = false` is the opt-out that preserves the real
object.

## Target capability

Take resources out of the state of a production configuration, deciding for each
one whether the real object must survive or disappear, and know when the
`removed` block gives up and `terraform state rm` must take over.

## Where the learner starts

In `challenge/work`, a complete and applicable `main.tf` describes a batch of
local end-of-life artefacts: `random_pet.jeton` (the name source, which stays
managed), `local_file.rapports` with a two-key `for_each`, `local_file.bacs` with
a three-key `for_each`, `local_file.cache` and `local_file.journaux`. No state
exists yet: the first move is an `init` then an `apply`, which creates seven
files and eight addresses.

A second file, `migration.tf`, holds two holed `removed` blocks (`from = ???`,
body `???`) and, as a comment, the false claim that acts as the trap: "the
`removed` block takes the resource out of the state; add `destroy = true` if you
also want to destroy the object". The plan will disprove it.

Both blocks are themselves **shipped commented out**, which makes the
configuration applicable as is: the learner uncomments them when needed. A third
block, for the journals, must be written from scratch.

## The state to reach

1. Both instances of `local_file.rapports` are gone from the state, but their two
   files are still on disk, content intact: they were forgotten, not destroyed.
2. `local_file.cache` is gone from the state **and** its file is gone from disk.
   Same `removed` block, without `destroy = false`: destruction is the default,
   and the comparison with point 1 proves it inside a single repository.
3. The `resource` block of every forgotten resource was removed from `main.tf`.
   Leaving both in place fails the plan with `Removed resource still exists`: a
   `removed` block is not a switch, it is the trace of a deletion already made in
   the configuration.
4. Only the `local_file.bacs["beta"]` instance left the state; the other two are
   still there and their three files are intact. The `removed` block refuses an
   instance key in its `from` (`Resource instance keys not allowed`): that
   granularity only exists through `terraform state rm 'local_file.bacs["beta"]'`.
5. The `for_each` of `local_file.bacs` no longer lists `beta`. Without that
   alignment, Terraform would immediately recreate the instance taken out of the
   state, and the bequeathed file would be overwritten.
6. The migration of `local_file.journaux` is **prepared but not applied**: its
   `resource` block is gone, its `removed` block with `destroy = false` is
   written, and the plan announces it without the learner running it. This is the
   documentation's own argument for preferring `removed` over `state rm`: the
   operation can be previewed, therefore reviewed as code.

## How it is proven

Tests query the structured state, never the learner's `.tf` file:

- `terraform show -json`: four addresses in `mode: managed` and not one more,
  `random_pet.jeton`, `local_file.bacs["alpha"]`, `local_file.bacs["gamma"]` and
  `local_file.journaux`. The absence of `local_file.rapports`, `local_file.cache`
  and `local_file.bacs["beta"]` is checked address by address.
- The filesystem settles the difference between forgetting and destroying: the
  six bequeathed files still exist and their content still carries the
  `random_pet.jeton` token read from the state, while the `local_file.cache` file
  is indeed gone.
- The plan converted to JSON holds exactly one non `no-op` change:
  `actions: ["forget"]` on `local_file.journaux`. That action only appears when
  the `removed` block carries `destroy = false`; with the default, the same
  configuration would produce `actions: ["delete"]`.
- `terraform plan -detailed-exitcode` therefore exits with **2**, and no plan
  entry concerns `local_file.bacs`: no `create` on `beta`, proof that the
  `for_each` was aligned after the `state rm`, and no `delete` on the other two.
- Two behaviour checks, played in a temporary copy and never touching the
  learner's work, prove what the lab teaches: a `removed` block targeting
  `local_file.bacs["alpha"]` fails on `Resource instance keys not allowed`, which
  justifies going through `terraform state rm`; and the same block deprived of
  `destroy = false` plans a `delete` on every remaining instance. If they turn
  red, the lab needs reviewing, not the submission.

## 🎯 Challenge: one end-of-life batch, four different decisions

### 📦 Starting point

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

### ✅ Objective

Carry out this batch migration, deciding resource by resource whether the real
object survives or disappears, and using the right way for each grain.

### 📋 What you must obtain

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

### ⚠️ The heart of the matter

Two boundaries decide everything, and neither can be guessed:

| What you want | What to write |
| --- | --- |
| Bequeath an object (it survives) | `removed` + `lifecycle { destroy = false }` |
| Delete an object | `removed` alone, or `destroy = true` |
| Take out **a single instance** of a `for_each` | `terraform state rm`, then drop the key from the `for_each` |

The `removed` block refuses an instance key in its `from`
(`Resource instance keys not allowed`), and it **destroys by default**. A mistake
there cannot be undone: the file is deleted, and the tests will see it.

### 🔍 Validation

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
