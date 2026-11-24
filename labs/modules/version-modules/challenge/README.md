# Publish three versions of a module, and consume them

## The situation

**Target exam sub-objective: 4c (refactor and version a module).**

A Git module is not versioned because someone wrote `version` somewhere: it is
versioned because a **reference** exists and a consumer points at it. Two traps
follow immediately: the `version` argument is refused outside a registry, and a
**tag moves**, which makes it a convenient reference but not an immutable one.

## Capability targeted

Publish a minor then a major version of a shared module, matching the number to
the nature of the change, then have **three** different revisions of that module
consumed by three root configurations, each with the reference form its need
calls for.

## Where the learner starts

`challenge/work` works **offline**, with no provider at all, and holds:

- `modules-src/etiquette/`: the module in version `1.0.0`, three files, a required
  `prefixe` variable, the `etiquette` and `version_module` outputs. The folder is
  **not** a Git repository yet: initialising it is the first move.
- `modules-src/CHANGELOG.md`: a single `1.0.0` entry, with a comment naming the
  two that are missing.
- `fige/main.tf`: `source = "???"`, correct arguments, must stay on `1.0.0`.
- `stable/main.tf`: `source = "???"` **and** a parasitic `version = "1.1.0"` line,
  inherited from a copy-paste of a registry block.
- `migre/main.tf`: `source = "???"` with the `1.0.0` arguments, to be adapted to
  the `2.0.0` rename.
- `CIBLE.md`: the three versions to publish, what each project must consume, and
  the two rules not to forget. No Git command appears in it.

## The state to reach

1. `modules-src` is a Git repository carrying three annotated tags, `v1.0.0`,
   `v1.1.0` and `v2.0.0`, on three distinct commits.
2. At tag `v1.1.0`, the module accepts an **optional** `suffixe` variable
   (`default = ""`), `prefixe` is still declared, and `version_module` is `1.1.0`:
   a configuration written for `1.0.0` still applies unchanged.
3. At tag `v2.0.0`, `prefixe` is **renamed** `nom_projet` and `version_module` is
   `2.0.0`. The old name is gone, which makes it a breaking change.
4. `fige/` consumes the module by the **SHA-1** of the `1.0.0` commit, and exposes
   `version_module = "1.0.0"`.
5. `stable/` consumes `?ref=v1.1.0`, **without** a `version` argument, and exposes
   `etiquette = "atelier-nord"`.
6. `migre/` consumes `?ref=v2.0.0`, its arguments adapted to the rename, and
   exposes `etiquette = "chantier"`.
7. All three projects are applied, so their outputs sit in their state.

## How it is proven

No test reads a `.tf` file written by the learner.

- The three `.terraform/modules/modules.json`, written by Terraform at install
  time: their `Source` gives the reference actually resolved, carrying points 4, 5
  and 6. A 40-hex-character `?ref=` distinguishes a SHA-1 from a tag name.
- The absence of a `Version` key in those entries: it exists only for a
  **registry** module. A present `modules.json` also proves the parasitic
  `version` line was removed, the `init` otherwise failing on `Invalid registry
  module source address`.
- `terraform output -json` in each project: `version_module` comes from the
  **resolved** module, it cannot be written from the root (points 1 to 6).
- The **installed** code under `.terraform/modules/`: `1.1.0` must still declare
  `prefixe` and declare `suffixe` **with** a `default`, `2.0.0` must declare
  `nom_projet` and **no longer** `prefixe` (points 2 and 3).

A bare `challenge/work` fails everywhere. Pointing `fige/` at tag `v1.0.0` instead
of the SHA-1 drops only the immutability test, and publishing a `1.1.0` whose
`suffixe` would be mandatory drops only the backwards-compatibility one.

## 🎯 Challenge: three published versions, three ways to consume them

### 📦 Starting point

`challenge/work` holds a library and three projects, all **offline**, with no
provider at all:

| Folder | What it is |
| --- | --- |
| `modules-src/etiquette/` | the module in **1.0.0**, to be evolved. **Not yet** a Git repository |
| `modules-src/CHANGELOG.md` | a single entry, two are missing |
| `fige/` | holed `source`, must stay on 1.0.0 |
| `stable/` | holed `source` **and** one `version` line too many |
| `migre/` | holed `source`, arguments to adapt |
| `CIBLE.md` | what each version must bring, and what each project must target |

### ✅ Objective

Publish **three** versions of the module, then wire the three projects onto them
with the reference form each one calls for.

### 📋 What you must obtain

1. `modules-src` is a Git repository with **three annotated tags** on **three
   distinct commits**: `v1.0.0`, `v1.1.0`, `v2.0.0`.
2. `1.1.0` adds an **optional** `suffixe` variable, keeps `prefixe`, and its
   `version_module` output is `1.1.0`.
3. `2.0.0` **renames** `prefixe` to `nom_projet`, and `version_module` is `2.0.0`.
4. `fige/` targets the **immutable** reference of the 1.0.0 commit, and exposes
   `version_module = "1.0.0"`.
5. `stable/` targets tag `v1.1.0`, **without** a `version` argument, and exposes
   `etiquette = "atelier-nord"`.
6. `migre/` targets tag `v2.0.0`, arguments adapted, and exposes
   `etiquette = "chantier"`.
7. All three projects are **applied**.

### ⚠️ The heart of the matter

A Git tag **moves**: `git tag -f` changes the designated commit without anything
moving on the consumer side, and a `terraform init -upgrade` then brings back
different code **under the same number**. Only one reference cannot be redefined.

| Form of `?ref=` | What it guarantees |
| --- | --- |
| absent | nothing: the **default branch**, which moves on every commit |
| a tag (`v1.1.0`) | the **published** version, as long as nobody moves the tag |
| a **SHA-1** | the **content**, definitively |

And the `version` argument exists **only** for a registry module. Next to a Git
source, the `init` stops on `Invalid registry module source address`.

The repository is local, so the source is a `git::file://` URL. Build it with
`path.cwd` so it does not depend on your own directory layout.

### 🔍 Validation

`dsoxlab check modules-version-modules` proves, by execution:

- the three `.terraform/modules/modules.json`, written by Terraform: their
  `Source` gives the reference **actually resolved**, and a 40-hex-character
  `?ref=` distinguishes a SHA-1 from a tag name;
- the absence of a `Version` key in those entries, reserved for registry modules;
- `terraform output -json`: `version_module` comes from the resolved module, it
  cannot be written from the root;
- the **installed** code under `.terraform/modules/`: 1.1.0 must still declare
  `prefixe` and declare `suffixe` **with** a `default`, 2.0.0 must declare
  `nom_projet` and no longer `prefixe`.

No test reads your `.tf` files.

Stuck? `dsoxlab hint modules-version-modules`.
