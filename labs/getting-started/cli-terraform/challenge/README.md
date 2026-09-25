# 🎯 Challenge: a chain that runs with nobody to read it

## Starting point

`challenge/work` holds a configuration resting on `local`, `null` and `random`:
no cloud, no VM, no cost. The directory is bare, with no `.terraform/`, no lock
file and no state.

**Three defects are placed deliberately** in `main.tf`, and its header announces
them:

1. the file is **not in canonical format**;
2. it references a variable **declared nowhere**;
3. **no output** exposes the computed values.

## ✅ Objective

Fix all three, **without changing what the configuration produces**, then run the
complete chain without a single interactive confirmation.

1. `terraform init` succeeding, lock file present.
2. No file outside canonical format any more.
3. `validate` with no diagnostic of severity `error`.
4. The configuration applied, state carrying exactly `random_pet.nom`,
   `local_file.rapport` and `null_resource.marqueur`.
5. Three outputs: `nom_animal`, `chemin_rapport` and `nom_majuscule`. The last
   one is an **expression**, not a copy.
6. A plan replayed after the apply announces nothing.

## 🧭 Order matters, and the first step surprises

**`validate` needs the providers' schemas.** Run before `init`, it fails for a
reason unrelated to your code's quality. Initialise first, or you will fix an
error that does not exist.

**`fmt` is not fixed by hand.** `terraform fmt -recursive` does the work, and
`-check` is there to verify, not to repair.

**An output is the only official channel towards a script.** A value not listed
there is unreachable from outside, short of digging into state, which amounts to
depending on an internal format.

## 🔍 Validation

```bash
dsoxlab check getting-started-cli-terraform
```

No test reads back your `.tf`, and none parses output meant for a human.
Everything goes through exit codes and JSON: `validate -json` for `valid` and
`error_count`, `output -json` for the values, `show -json` for state.

An expression is evaluated **outside an interactive session**, by passing it on
the standard input of `terraform console`, and its result is compared to the
expected value: that is how a computation is proven without reading the code that
performs it.

And `plan -detailed-exitcode` must exit **0**. A 2 would signal drift, a 1 an
error: without that flag, all three cases look alike.

Stuck? `dsoxlab hint getting-started-cli-terraform`.
