# Scenario: bequeath an infrastructure without destroying it, with the removed block

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
