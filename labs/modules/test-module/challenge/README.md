# 🎯 Challenge: write the suite that proves the module

## 📦 Starting point

`challenge/work` runs **offline**, with no provider at all:

| File | What it is |
| --- | --- |
| `etiquette/` | the module, **complete**, not to be modified |
| `etiquette/tests/etiquette.tftest.hcl` | the suite skeleton, four `run` blocks as `???` |
| `CIBLE.md` | the module contract and the four behaviours to cover |

## ✅ Objective

Write the `.tftest.hcl` suite of the `etiquette` module, so that `terraform test`
passes **and** so that it fails if the module changes behaviour.

## 📋 What you must obtain

1. `terraform test`, run from `etiquette/`, exits **0**.
2. The JSON summary reports `status: pass`, no failure, at least **four**
   successful `run` blocks.
3. One `run` covers the **default**: with `prefixe` alone, the label is `atelier`
   and its length `7`.
4. One `run` covers the **suffix**: `atelier-nord`.
5. One `run` covers **uppercase**: `ATELIER`.
6. One `run` covers the **refusal** of a prefix shorter than three characters,
   applying nothing.
7. The suite is **re-runnable** and leaves no `*.tfstate` in the module directory.

## ⚠️ The heart of the matter

A suite that asserts nothing **goes green**:

```text
$ terraform test
Success! 4 passed, 0 failed.
```

That is why this lab's validation does not read your suite: it **breaks the
module**, one behaviour at a time, in a temporary copy, and requires your suite to
notice. Four mutations are played: the prefix `validation` disappears, the
`suffixe` default changes, the hyphen becomes an underscore, the uppercase pass is
removed.

The fourth behaviour, the **refusal**, is not written like the others: there is
nothing to assert when nothing must be produced. The failure itself is what is
expected, and you must **name** the object supposed to produce it. A workaround via
an assertion will be spotted: the matching mutation must produce
`Error: Missing expected failure`.

## 🔍 Validation

`dsoxlab check modules-test-module` proves, by execution:

- a **control**: the suite passes on the intact module, without which the mutations
  would prove nothing;
- **four mutations**, each of which must make your suite fail;
- the **exit code** of `terraform test`, and the `test_summary` of the `-json`
  stream: `status`, `passed`, `failed`, `errored`;
- **re-runnability**: the suite is run twice, and the module directory must keep no
  state.

Stuck? `dsoxlab hint modules-test-module`.
