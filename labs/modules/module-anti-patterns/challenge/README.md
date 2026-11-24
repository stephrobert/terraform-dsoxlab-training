# Refactor a copy-pasted project without destroying anything

## The situation

**Target exam sub-objective: 4d (refactor an existing configuration into
modules).**

Terraform tracks **addresses**, not resources. Extracting copy-pasted code into a
module changes those addresses, and without an explicit declaration the tool
destroys and recreates. The lab therefore imposes the constraint that makes the
exercise realistic: the project is **already applied**.

## Capability targeted

Replace two copy-pasted blocks with a typed module called once, declaring the
address moves so that no resource is destroyed, and prove that last point from a
witness Terraform cannot recompute.

## Where the learner starts

`challenge/work` runs **offline**, with the `local` and `random` providers:

- `projet/main.tf`: two `local_file` and two `random_pet`, declared loosely at the
  root, with hardcoded values.
- `projet/outputs.tf`: the `chemins` and `jetons` outputs, whose shape must not
  change.
- `projet/terraform.tfstate` and `projet/plaques/*.txt`: the project is **already
  applied**, as a teaching fixture.
- `CIBLE.md`: the three defects, the state to reach, and the prohibition.

## The state to reach

1. A `bibliotheque/plaque/` module carries the resource, written **once**.
2. The project calls it **twice** from a **single** block.
3. The module input is an **object**, and every variable and output carries a
   `description`.
4. The two state tokens are **unchanged**: nothing was destroyed.
5. The plan announces **no** change any more.
6. The `chemins` and `jetons` outputs keep their shape.
7. The tree stays **flat**: the module calls no other.

## How it is proven

No test reads a `.tf` file.

- The state, via `terraform show -json`: every resource must live under `module.`,
  and the `random_pet` **tokens** must be **exactly** those of the starting state.
  The witness is chosen deliberately: a `local_file` `id` is a hash of its content,
  hence **identical** after a destroy-and-recreate, whereas a `random_pet` is drawn
  at random.
- The plan JSON: a **single** `module_calls`, one of whose arguments references
  `each` or `count`; no `create` or `delete` action in `resource_changes`; no
  nested module inside the called module.
- The `description` of the module's variables and outputs, exposed in that same
  JSON.
- `plan -detailed-exitcode` at 0.

A control keeps those checks honest: the no-destruction tests only run if the
refactoring actually **happened**, otherwise an untouched `challenge/work` would
satisfy them all.

A bare `challenge/work` scores 0 out of 8. The same refactoring **without** `moved`
blocks destroys and recreates all four resources, and drops only the token test.
Two copy-pasted calls instead of a `for_each` drop only the single-call test.

## 🎯 Challenge: refactor without destroying anything

### 📦 Starting point

`challenge/work` runs **offline** and the project is **already applied**:

| File | What it is |
| --- | --- |
| `projet/main.tf` | two `local_file` and two `random_pet`, **copy-pasted** at the root |
| `projet/outputs.tf` | the `chemins` and `jetons` outputs, whose shape must not change |
| `projet/terraform.tfstate` | the **starting** state: those resources already exist |
| `CIBLE.md` | the three defects to fix, and the prohibition |

### ✅ Objective

Replace the copy-paste with a **typed** module, called **once**, without destroying
or recreating anything.

### 📋 What you must obtain

1. A `bibliotheque/plaque/` module carries the resource, written **once**.
2. The project calls it **twice** from a **single** block.
3. The module input is an **object**, and every variable and output carries a
   `description`.
4. The state **tokens** are unchanged.
5. `terraform plan` announces **no** change any more.
6. The outputs keep their shape.
7. The module calls **no** other module.

### ⚠️ The heart of the matter

Terraform tracks **addresses**. Moving a resource without declaring it gives:

```text
Plan: 4 to add, 0 to change, 4 to destroy.
```

There is a block, made for this, that declares one address replaces another. With
it, the plan becomes:

```text
  # local_file.plaque_nord has moved to module.plaque["nord"].local_file.plaque

Plan: 0 to add, 0 to change, 0 to destroy.
```

The witness of the check is the `random_pet` **token**, not the file `id`: the
latter is only a hash of the content, hence **identical** after a
destroy-and-recreate.

### 🔍 Validation

`dsoxlab check modules-module-anti-patterns` proves, by execution:

- the state: every resource under `module.`, and both tokens **unchanged**;
- the plan JSON: a **single** module call referencing `each` or `count`, no
  `create` or `delete` action, no nested module;
- the `description` of the module's variables and outputs;
- `plan -detailed-exitcode` at 0.

The no-destruction tests only run once the refactoring is done: without that,
touching nothing would satisfy them.

Stuck? `dsoxlab hint modules-module-anti-patterns`.
