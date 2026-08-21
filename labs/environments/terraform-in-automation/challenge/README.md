# 🎯 Challenge: a chain judged on its exit codes

## 📦 Starting point

| File | What it is |
| --- | --- |
| `main.tf` | **incomplete**: one marker and one command to write |
| `pipeline.sh` | skeleton: five steps stubbed with `???`, plus the code recording |
| `.gitignore` | **incomplete**: it lets the plan file through |
| `CIBLE.md` | the expected format of the six proof files |

Nothing is initialised, no state, no `preuves/`.

## ✅ What you must achieve

1. The configuration is formatted, valid, initialised without a prompt, applied
   **from a saved plan file**, and converged. The apply lasts **at least ten
   seconds**.
2. `preuves/chaine.json`: the exit code of each of the **five** steps.
3. `preuves/codes.json`: the **three** values of `plan -detailed-exitcode`, and
   the code of `fmt -check` on a badly indented file.
4. `preuves/prompt.json`: the code **and the waiting time** of a
   `plan -input=false` with no value for a variable.
5. `preuves/plan_fige.json`: the fate of **four** options passed to the apply of
   a saved plan, each being `erreur` or `ignore`.
6. `preuves/verrou.json`: the `-lock-timeout` default, and the code of a plan
   launched **during** an apply, with that default then with a sufficient delay.
7. `preuves/fuite.json`: the exact `jq` path where the secret leaks in clear from
   the saved plan. And the `.gitignore` really excludes that file.

## ⚠️ Three things not to assume

The exit code of `fmt -check` on a badly indented file **is not 1**.

A `plan -input=false` with no variable value **does not wait**: measure its time
rather than assuming it.

When applying a saved plan, **only one** of the four options makes the command
fail. The others are accepted, and **ignored**.

## 🔍 Validation

`dsoxlab check environments-terraform-in-automation` **replays** every claim of
yours: it re-runs `fmt -check`, the three plans, the concurrent apply under lock
and the four saved-plan options, then compares against your records. A number
copied from a course instead of measured will fail.

The `.gitignore` is put to work by `git check-ignore` in a throwaway repository.

Stuck? `dsoxlab hint environments-terraform-in-automation`.
