# 🎯 Challenge: the commands the exam expects, performed rather than recited

## 📦 Starting point

`challenge/work` is not initialised. It holds a configuration that does not
stand up, and a file nobody created with Terraform.

| File | What it has |
| --- | --- |
| `versions.tf` | complete. Three local providers, no VM, no cloud account |
| `variables.tf` | complete. One variable per rung of the cascade |
| `main.tf` | **badly indented**, with a `???` hole in it |
| `outputs.tf` | five outputs, all of them holes |
| `terraform.tfvars` | empty, to be filled |
| `env.auto.tfvars` | empty, to be filled |
| `etat/preexistant.txt` | **already on disk**, waiting to be adopted |

No `.terraform/`, no state, no `preuves/` directory.

## ✅ What you must reach

1. **`preuves/codes.json`** records the exit codes of six gestures, taken as
   you perform them:

   | Key | The gesture |
   | --- | --- |
   | `validate_avant_init` | `validate` run before any `init` |
   | `validate_configuration_valide` | `validate` on the repaired configuration |
   | `validate_attribut_absent` | `validate` on a variant carrying an attribute no schema defines |
   | `fmt_check_avant` | `fmt -check` on the badly indented `main.tf` |
   | `fmt_check_apres` | `fmt -check` once reformatted |
   | `plan_avant_convergence` | `plan -detailed-exitcode` before the first apply |

2. The configuration **converges**: `plan -detailed-exitcode` exits 0, and so
   does `fmt -check -recursive`.

3. The first four outputs name the winner of the precedence cascade. Every
   variable is set by **several sources at once**: only one wins, and the name
   of the value says which.

   The environment variables to export are part of the brief:

   ```bash
   export TF_VAR_par_environnement="gagnant-environnement"
   export TF_VAR_par_fichier="perdant-environnement"
   export TF_VAR_par_ligne_de_commande="perdant-environnement"
   ```

   Spreading the rest across `terraform.tfvars`, `env.auto.tfvars` and `-var`
   so that each output returns `gagnant-<its source>` is your job.

4. A **`moved`** block has renamed `random_pet.ancien_nom`, and it has been
   **applied**: the old address is gone from state.

5. An **`import`** block has brought `terraform_data.provisionne_ailleurs`
   under management, with its existing id, `identifiant-connu`.

6. A **`removed`** block has dropped `local_file.adopte` from state **without
   destroying the file**: `etat/preexistant.txt` is still there, contents
   intact.

7. **`preuves/plan-replace.json`** is a saved plan asking for the replacement
   of `null_resource.a_remplacer`, and of nothing else.

8. `identifiant_sensible` is marked **sensitive**.

## ⚠️ The heart of it

Two things are expensive on exam day.

**`validate` is not a spell checker.** It needs the providers' **schemas**: run
before `init` it validates nothing, and says so with a non-zero code. Once the
schemas are in place it catches an attribute that does not exist, which "it
only checks syntax" suggested was impossible.

**`fmt -check` returns 3, not 1.** A CI script testing `-eq 1` would wave
through every unformatted file.

And a third one, discovered while writing this lab: **`init` parses the
configuration**. So it fails on a `???`, with a message about ternary operators
that sends you looking in the wrong place. Fix the `???` before initialising.

Finally, `removed` without `lifecycle { destroy = false }` **destroys** the
object instead of releasing it. One word apart, and the file is gone.

## 🔍 Validation

`dsoxlab check certifications-associate-essential-commands` proves, by running
things:

- that the six codes in `codes.json` are the ones **your** configuration
  produces: the tests replay all six gestures in throwaway copies and compare.
  A miscopied number falls;
- that each rung of the cascade names its winner, read from `output -json`;
- that `moved` was **applied**, not merely planned;
- that the imported resource carries the existing id, and was therefore not
  created;
- that `removed` left the file **intact on disk** while state forgot it;
- that the replacement plan targets a single address, `delete` then `create`;
- that the sensitive value is masked on screen **and readable in clear text in
  state**: `sensitive` hides a display, it encrypts nothing;
- that in the end the configuration converges and holds canonical format.

No test opens your `main.tf`, and none reads a message meant for a human.

Stuck? `dsoxlab hint certifications-associate-essential-commands`.
