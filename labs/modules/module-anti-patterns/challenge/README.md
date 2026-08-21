# 🎯 Challenge: refactor without destroying anything

## 📦 Starting point

`challenge/work` runs **offline** and the project is **already applied**:

| File | What it is |
| --- | --- |
| `projet/main.tf` | two `local_file` and two `random_pet`, **copy-pasted** at the root |
| `projet/outputs.tf` | the `chemins` and `jetons` outputs, whose shape must not change |
| `projet/terraform.tfstate` | the **starting** state: those resources already exist |
| `CIBLE.md` | the three defects to fix, and the prohibition |

## ✅ Objective

Replace the copy-paste with a **typed** module, called **once**, without destroying
or recreating anything.

## 📋 What you must obtain

1. A `bibliotheque/plaque/` module carries the resource, written **once**.
2. The project calls it **twice** from a **single** block.
3. The module input is an **object**, and every variable and output carries a
   `description`.
4. The state **tokens** are unchanged.
5. `terraform plan` announces **no** change any more.
6. The outputs keep their shape.
7. The module calls **no** other module.

## ⚠️ The heart of the matter

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

## 🔍 Validation

`dsoxlab check modules-module-anti-patterns` proves, by execution:

- the state: every resource under `module.`, and both tokens **unchanged**;
- the plan JSON: a **single** module call referencing `each` or `count`, no
  `create` or `delete` action, no nested module;
- the `description` of the module's variables and outputs;
- `plan -detailed-exitcode` at 0.

The no-destruction tests only run once the refactoring is done: without that,
touching nothing would satisfy them.

Stuck? `dsoxlab hint modules-module-anti-patterns`.
