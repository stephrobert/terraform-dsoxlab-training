# What the essential commands really answer

## The situation

**Exam objective targeted: 3d, generate and review an execution plan.**
Supporting objectives: 3c (validate a configuration), 3g (formatting and
style), 4c (variables and outputs), 4h (sensitive data), 6d (state and
drift), 7a (import existing infrastructure) and 7b (inspect state with the
CLI).

The Associate 004 is a one-hour multiple-choice exam on Terraform 1.12: you
type nothing, and that is the trap. Revising a table of commands feels like
knowing them, right up to the question about what a command **refuses** to do.

## Capability targeted

Establish experimentally the exact behaviour of the workflow commands: their
exit code, their prerequisites, and the line between what they change and what
they merely read. The question driving the lab is not "what does `validate`
do", it is "can it answer without `init`, and what does it catch".

## Where the learner starts

A `shell` lab: everything happens in `challenge/work`, on the `local`, `null`
and `random` providers only, with no VM and no cloud account. The directory
holds a `main.tf` that is badly indented and holed by a `???` (a resource name,
an output to mark sensitive), a variable seeded in a `default`, an incomplete
`terraform.tfvars` and `*.auto.tfvars`, and a file `etat/preexistant.txt`
already on disk, created by nobody, waiting to be adopted. No `.terraform/`, no
state, no `preuves/` directory.

## The state to reach

1. The directory is initialised and the configuration converges:
   `plan -detailed-exitcode` exits 0, and state describes the expected
   resources as `mode: managed`.
2. `preuves/codes.json` records the exit codes observed for six gestures:
   `validate` before any `init`, then on the valid initialised configuration,
   then on a variant where an attribute does not exist, `fmt -check` before and
   after reformatting, and `plan -detailed-exitcode` before convergence.
3. Four outputs name the winner of the precedence cascade between `default`,
   `TF_VAR_`, `terraform.tfvars`, `*.auto.tfvars` and `-var`.
4. A `moved {}` block has renamed a resource (old address gone from state, new
   one present, plan at zero changes) and an `import {}` block has brought
   `etat/preexistant.txt` under Terraform management without touching its
   contents.
5. A `removed {}` block carrying `lifecycle { destroy = false }` has dropped a
   resource from state while the file it managed still exists.
6. `preuves/plan-replace.json` is a saved plan explicitly requesting the
   replacement of one resource.
7. One output is marked sensitive, and its value stays readable in clear text
   in state.

## How it is proven

The tests run inside `challenge/work`, never open the learner's `main.tf`, and
read no output meant for a human.

- The six gestures of point 2 are replayed in throwaway copies of the
  directory: the tests record the codes themselves, against your configuration,
  and compare them to those in `codes.json`. A miscopied number falls. This is
  where the received idea gives way: `validate` without `init` exits in error,
  and it catches an unknown attribute, which "syntax only" suggested was
  impossible. That replay mostly serves the lab's own correctness: the day a
  Terraform version changes one of these codes, it is the replay that says so,
  rather than a blameless candidate being failed.
- Precedence is read from `output -json`, hence from the state **your** apply
  produced. The tests apply nothing themselves: they merely put in their
  environment the `TF_VAR_` values the brief fixes, without which the
  environment variable would fall back to its `default`.
- Points 4 and 5 are read from `show -json`: addresses present or absent,
  `mode: managed`, cross-checked against the files on disk. Point 5 only passes
  if state forgot the resource while the file survived, which is the opposite
  of the `removed` pitfall.
- Point 6 is checked on the plan converted to JSON: `actions` is
  `["delete", "create"]` and the plan touches that address alone. Point 7
  crosses `output -json`, which reports `"sensitive": true`, with the state
  file, where the same value appears in clear text: masking is a display
  convenience, not encryption.
- None of this passes on an empty directory, nor on a configuration that was
  never applied.

## 🎯 Challenge: the commands the exam expects, performed rather than recited

### 📦 Starting point

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

### ✅ What you must reach

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

### ⚠️ The heart of it

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

### 🔍 Validation

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
