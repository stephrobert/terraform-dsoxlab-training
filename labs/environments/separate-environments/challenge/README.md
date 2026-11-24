# Two roots, two states, one shared module

## The situation

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

## 🎯 Challenge: two genuinely isolated environments

### 📦 Starting point

`challenge/work` runs **offline**, `local` backend:

| Folder | What it is |
| --- | --- |
| `modules/plaque/` | the shared module, **complete** |
| `envs/dev/` | root, empty `backend "local" {}`, holed module call |
| `envs/prod/` | the same, with other values |
| `CIBLE.md` | the per-environment values and the initialisation command |

### ✅ Objective

Give each environment its own **state**, without duplicating the module or the
backend block.

### 📋 What you must obtain

1. Both roots call the shared module by a **relative** path.
2. `dev` produces **one** plate, `prod` produces **three**.
3. `etats/dev.tfstate` and `etats/prod.tfstate` exist, **outside** the roots.
4. The `backend` block stays **empty**: the path comes from `-backend-config`.
5. Both environments converge.

### ⚠️ The heart of the matter

A `backend` block accepts **no** named value:

```text
Error: Variables not allowed

Variables may not be used here.
```

Hence **partial configuration**: the block stays empty, identical everywhere, and
the missing arguments arrive at initialisation.

```bash
terraform init -backend-config=<your-file>.hcl
```

And the official argument against workspaces here is not ergonomics: "CLI
workspaces within a working directory use the **same backend**", therefore a single
set of credentials for every environment.

### 🔍 Validation

`dsoxlab check environments-separate-environments` proves, by execution:

- the backend configuration **recorded** by each root, in
  `.terraform/terraform.tfstate`;
- the resource count and outputs of each state;
- the sharing of the **same** module, read in both `modules.json`;
- **isolation**: a real `destroy` in `dev`, played on a copy, must leave `prod`'s
  state intact.

Stuck? `dsoxlab hint environments-separate-environments`.
