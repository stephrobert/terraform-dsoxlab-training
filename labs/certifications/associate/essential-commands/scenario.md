# Scenario: what the essential commands really answer

**Exam objective targeted: 1b, generate and review an execution plan.**

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
