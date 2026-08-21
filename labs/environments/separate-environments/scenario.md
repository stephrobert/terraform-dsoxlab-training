# Scenario: two roots, two states, one shared module

**Target exam sub-objective: 3b (backends and partial configuration).**

Two environment directories separate nothing until their **states** are distinct.
And the state path cannot be parameterised by a variable: a `backend` block refuses
any named value. **Partial** configuration is the official answer.

## Capability targeted

Wire two root configurations onto a shared module, give each its own state through
partial backend configuration, then prove isolation by destroying one of the two
environments.

## Where the learner starts

`challenge/work` runs **offline**, `local` backend:

- `modules/plaque/`: the shared module, complete, two inputs and two outputs.
- `envs/dev/main.tf` and `envs/prod/main.tf`: **identical**, with an empty
  `backend "local" {}` already written and a holed module call.
- `CIBLE.md`: the values expected per environment, the `Variables not allowed`
  error that explains the empty block, and the initialisation command.

## The state to reach

1. Each root calls the shared module by a **relative** path.
2. `dev` produces **one** plate, `prod` produces **three**.
3. Each root drives its own state, `etats/dev.tfstate` and `etats/prod.tfstate`,
   **outside** the root directories.
4. Both backends are configured with `-backend-config`, the block staying empty.
5. Both environments are applied and converge.

## How it is proven

- Each root's `.terraform/terraform.tfstate` carries the **retained** backend
  configuration: its `config.path` must differ between roots and carry the
  environment name.
- `terraform show -json` per root: the resource **count**, the exposed environment,
  and the produced paths.
- Both `modules.json` must designate the **same** module folder, through a `../`
  `Source`.
- **The isolation proof**: the tests copy the work, run a real `destroy` in `dev`,
  and require `prod`'s state to be **unchanged**, address by address.
- `plan -detailed-exitcode` at 0 in both.

A bare `challenge/work` scores 0 out of 6. Pointing `prod` at `dev`'s state drops
four tests, including the isolation one. Duplicating the module in each root drops
only the shared-module test.
