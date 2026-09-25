# Scenario: split a configuration without changing the plan

**Target exam sub-objective: 1b (generate an execution plan)**, comparing
two plans being the only proof the split changed nothing.

Splitting a `main.tf` is presented everywhere as risk-free because `terraform
validate` passes afterwards. Yet `validate` "does not check if argument values are
valid for a specific provider [...] It does not evaluate any existing state": a
block lost in the copy-paste passes it without a word. The only proof of invariance
is **comparing two plans**.

## Capability targeted

Split a monolithic configuration along the official file layout, proving by plan
comparison that the result is **unchanged**, then make the repository correct:
recursive formatting and a `.gitignore` that ignores artefacts without ignoring the
lock file.

## Where the learner starts

`challenge/work` runs **offline**, with the `local` and `random` providers:

- `projet/main.tf`: eighty lines carrying **everything**, the `terraform` block,
  providers, three variables, three resources one of which depends on the other
  two, and three outputs.
- `CIBLE.md`: the expected layout, the invariant to preserve, and the repository
  rules.

## The state to reach

1. The layout is in place: `terraform.tf`, `providers.tf`, `variables.tf`,
   `outputs.tf`, and a `main.tf` keeping only the resources.
2. `terraform.tf` carries **one** `terraform` block and **no** `provider`.
3. Variables and outputs are declared in **alphabetical order**.
4. The plan is **identical** to that of the monolithic configuration.
5. `terraform fmt -check -recursive` exits **0**.
6. A `.gitignore` ignores `.terraform/`, the state, its backups and the saved plan
   **without extension**, but lets `.terraform.lock.hcl` through.

## How it is proven

- The tests **replan** the monolithic fixture in a temporary directory, and compare
  its fingerprint with the learner's plan: `planned_values`, `resource_changes`,
  `output_changes` and `variables`. The `configuration` section is deliberately
  **excluded**, since it reflects the split.
- A control only runs those invariance checks if the layout exists: without it, an
  untouched `challenge/work` would trivially equal itself.
- The layout, the single `terraform` block and the alphabetical order are read in
  the files, which here are the **deliverable**.
- `terraform fmt -check -recursive` is run from the workdir **root**.
- The `.gitignore` is put to work by `git check-ignore` in a throwaway **copy**
  initialised as a repository: that is the verdict git would really apply,
  negation patterns included.

A bare `challenge/work` scores 0 out of 8. A split that **loses** a resource passes
`terraform validate` with `Success!` and drops only the plan comparison test. Naming
the file `versions.tf` instead of `terraform.tf` drops the layout test and, with it,
the checks that depend on it.
