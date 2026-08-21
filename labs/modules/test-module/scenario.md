# Scenario: prove a module with its own test suite

**Target exam sub-objective: 4d (test a module).**

An assertion that passes proves nothing: this lab demands a suite that **fails
when the module breaks**. `terraform test` runs against the configuration of the
**current directory**, so a suite placed in `<module>/tests/` tests the module
itself, with no wrapping root configuration.

## Capability targeted

Write a module's `.tftest.hcl` suite so that it covers its **default** behaviour,
each of its **options**, and its **refusal** of an invalid input, then prove that
suite actually detects a regression.

## Where the learner starts

`challenge/work` runs **offline**, with no provider at all:

- `etiquette/`: the module, **complete**, not to be modified. A required `prefixe`
  variable with a length `validation`, two optional variables `suffixe` and
  `majuscules`, the `etiquette` and `longueur` outputs.
- `etiquette/tests/etiquette.tftest.hcl`: the suite skeleton, four `run` blocks
  whose names, conditions and messages are `???`.
- `CIBLE.md`: the module contract and the four behaviours to cover, without giving
  the syntax.

## The state to reach

1. The suite lives in `etiquette/tests/` and carries the `.tftest.hcl` extension.
2. `terraform test` exits **0** from the module directory.
3. The JSON summary reports `status: pass`, no failure, and at least **four**
   successful `run` blocks.
4. One `run` covers the **default**: with `prefixe` alone, the label is `atelier`
   and its length `7`.
5. One `run` covers the **suffix**: `atelier-nord`, hyphen included.
6. One `run` covers **uppercase**: `ATELIER`.
7. One `run` covers the **refusal** of a too-short prefix, applying nothing, and
   declaring the object expected to fail.
8. The suite is **re-runnable** and leaves no state behind.

## How it is proven

Since the deliverable is a test suite, reading it would prove nothing: a suite
without assertions passes and exits 0. The tests therefore **mutate** the module in
a temporary directory, one behaviour at a time, and require the learner's suite to
notice.

- A **control** first checks the suite passes on the **intact** module. Without it,
  a missing suite would fail every mutant, and the mutation tests would pass
  without a single assertion having been written.
- **Four mutations**: the `validation` removed, the `suffixe` default changed, the
  `-` separator replaced with `_`, the `upper()` dropped. Each must make the suite
  fail.
- The `validation` mutation must additionally produce
  `Error: Missing expected failure`, which proves `expect_failures` was used rather
  than a workaround assertion.
- The `terraform test -json` stream provides the machine summary, `test_summary`,
  with `status`, `passed`, `failed` and `errored`.
- The suite is run **twice** in a row, and the module directory must hold no
  `*.tfstate` afterwards.

A bare `challenge/work` scores 1 test out of 9. A suite of four `run` blocks with
**no assertion at all** passes `terraform test` but drops 5 tests: exactly the case
the mutations exist to catch.
