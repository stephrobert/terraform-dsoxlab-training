# Pro · Objective 2, dynamic configuration and troubleshooting

## The situation

**Exam objective targeted: 2** (2a validate the configuration, 2b data sources,
2c HCL functions, 2d meta-arguments, 2e variables and outputs in complex types,
2f sensitive data).

## Capability targeted

Produce a configuration **driven by data**: a single complex-typed input
generates N correctly named resources, with no duplicated code. And know how to
**repair** a configuration that does not validate.

## Where the learner starts

In `challenge/work`, a configuration that **fails `terraform init`**: three
deliberate errors are planted there (a forbidden combination of meta-arguments,
an incompatible type, a reference to an undeclared variable).

They do not all fall at the same time, and that is part of the lesson. `init`
parses the configuration, so it refuses the first one; while it does, no
provider is installed and `validate` answers `Missing required provider`, which
sends you looking in the wrong place. The two others appear together afterwards,
with their line numbers.

An `environnements` variable of type `map(object({...}))` describes several
environments with different sizes and options. The resources use the `null`,
`local`, `random` and `archive` providers: no cloud, everything local and free.

## The state to reach

1. `terraform validate` passes: the three errors are fixed.
2. A `for_each` over the map produces **exactly as many resources as there are
   entries**, each named by an HCL function normalising the key (lowercase,
   prefix, bounded length).
3. A `dynamic` block generates a variable number of nested blocks according to
   the options present in each object.
4. A sensitive value is exposed as an output **without leaking in clear text**.
5. The outputs expose an aggregated structure (a derived map), not a list of raw
   values.

## How it is proven

- `terraform validate -json` reports `valid: true`, a boolean rather than a text
  that changes between versions.
- State is read as JSON: the instances produced by the `for_each` are counted and
  their index checked to be the map **key**, never an integer, and the computed
  names are compared, key by key, with what the function must produce.
- The manifest is deserialised: it must be valid JSON, and its `etiquette` must
  equal the id of that environment's `random_pet`, which proves it is referenced
  rather than copied.
- The `dynamic` is proven by the **number** of `source` blocks per archive: the
  fixed block plus one per option. The environment with no option must carry the
  fixed block alone, which an `if` placed in the `content` would not achieve.
- `terraform output -json`: the sensitive output is marked `"sensitive": true`
  and masked in the human display.
- The decisive test **changes the variable**: it copies the directory, adds a
  fourth environment, applies, and requires four manifests, a normalised name for
  a key never seen before, and an archive with four blocks. Every other test
  would pass on a hand-written configuration; this one would not.
- Idempotence: a second plan exits 0.

## 🎯 Challenge: repair, then let the data drive

### 📦 Starting point

`challenge/work` holds a configuration that **does not pass `terraform init`**.

| File | State |
| --- | --- |
| `versions.tf` | **supplied**, four local providers |
| `variables.tf` | **supplied**, three environments in a `map(object)` |
| `main.tf` | **three errors** planted, and values to complete |
| `outputs.tf` | three outputs to write |

The values marked "À COMPLÉTER" are syntactically correct and **functionally
wrong**: the configuration will validate before doing what it is asked.

### ⚠️ Start with `init`, not with `validate`

`init` **parses** the configuration. While a structural error remains, no
provider is installed, and `validate` answers `Missing required provider`, which
has nothing to do with your errors.

The method: **init, fix what it refuses, init again, then validate**. The two
other errors then appear together, with their line numbers.

### ✅ Objective

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

### 🧭 Two traps that decide the rest

**`count` or `for_each`, and the choice is not neutral.** `count` addresses by
position: removing the middle entry shifts the following ones, which are
destroyed and recreated. `for_each` addresses by key and touches only what you
remove.

**A `dynamic`'s filtering happens in its `for_each`.** An `if` in the `content`
does not reduce the number of blocks: at that point the block is already decided.

### 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone2-dynamic-config
```

Nine tests, reading `validate -json`, `show -json` and `output -json`.

The last one is the one that counts: it copies your directory, **adds a fourth
environment**, applies, and requires everything to follow. Every other test would
pass on a configuration hand-written for these three precise environments; that
one would not.

Stuck? `dsoxlab hint certifications-professional-capstone2-dynamic-config`.
