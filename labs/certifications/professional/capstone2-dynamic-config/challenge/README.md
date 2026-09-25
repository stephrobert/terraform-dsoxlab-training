# 🎯 Challenge: repair, then let the data drive

## 📦 Starting point

`challenge/work` holds a configuration that **does not pass `terraform init`**.

| File | State |
| --- | --- |
| `versions.tf` | **supplied**, four local providers |
| `variables.tf` | **supplied**, three environments in a `map(object)` |
| `main.tf` | **three errors** planted, and values to complete |
| `outputs.tf` | three outputs to write |

The values marked "À COMPLÉTER" are syntactically correct and **functionally
wrong**: the configuration will validate before doing what it is asked.

## ⚠️ Start with `init`, not with `validate`

`init` **parses** the configuration. While a structural error remains, no
provider is installed, and `validate` answers `Missing required provider`, which
has nothing to do with your errors.

The method: **init, fix what it refuses, init again, then validate**. The two
other errors then appear together, with their line numbers.

## ✅ Objective

1. **Fix the three errors**: a forbidden combination of meta-arguments, an
   incompatible type, an undeclared variable.
2. **Normalise the names** with HCL functions: `PreProd_EU` must become
   `lab-preprod-eu`.
3. **The manifest** is JSON serialised **by a function**, carrying `nom`,
   `taille` and `etiquette` (this environment's `random_pet` id, **referenced**).
4. **A `dynamic` block** generating one `source` block per option. An
   environment with no option produces none.
5. **Three outputs**: an aggregated map indexed by normalised name, the secrets
   (sensitive), and the archive count.

## 🧭 Two traps that decide the rest

**`count` or `for_each`, and the choice is not neutral.** `count` addresses by
position: removing the middle entry shifts the following ones, which are
destroyed and recreated. `for_each` addresses by key and touches only what you
remove.

**A `dynamic`'s filtering happens in its `for_each`.** An `if` in the `content`
does not reduce the number of blocks: at that point the block is already decided.

## 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone2-dynamic-config
```

Nine tests, reading `validate -json`, `show -json` and `output -json`.

The last one is the one that counts: it copies your directory, **adds a fourth
environment**, applies, and requires everything to follow. Every other test would
pass on a configuration hand-written for these three precise environments; that
one would not.

Stuck? `dsoxlab hint certifications-professional-capstone2-dynamic-config`.
