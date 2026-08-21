# 🎯 Challenge: three published versions, three ways to consume them

## 📦 Starting point

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

## ✅ Objective

Publish **three** versions of the module, then wire the three projects onto them
with the reference form each one calls for.

## 📋 What you must obtain

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

## ⚠️ The heart of the matter

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

## 🔍 Validation

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
