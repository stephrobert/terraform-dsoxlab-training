# A test suite that cannot fail proves nothing

`terraform test` runs `.tftest.hcl` files against the configuration of the
**current directory**. A module is therefore tested **from its own directory**,
with no wrapping root configuration: the module outputs are read there directly as
`output.<name>`.

## The anatomy of a suite

```hcl
variables {
  prefixe = "atelier"
}

run "defaut" {
  assert {
    condition     = output.etiquette == "atelier"
    error_message = "Sans suffixe, l'etiquette doit valoir le prefixe seul."
  }
}
```

Three levels to keep apart. The **file-level** `variables` block applies to every
`run`. A `variables` block **inside a `run`** wins for that run. And each `run` may
carry several `assert` blocks, each with its own `error_message`, which is what you
will read when it fails.

## `apply` by default, `plan` on request

A `run` **applies** by default: "By default, each `run` block executes with
`command = apply`". That is what lets you assert values computed from resources
actually created, and it is also what creates them **for real**:

```text
$ ls -A plaques
      ← empty: the file was indeed created, then destroyed at teardown
```

The directory itself remains. Remember that `terraform test` **creates**
infrastructure and destroys it at the end, which the documentation states plainly:
"This command creates real infrastructure and will attempt to clean up the testing
infrastructure on completion."

When only the **plan** interests you, say so:

```hcl
run "verifie_sans_creer" {
  command = plan

  assert {
    condition     = output.etiquette == "atelier"
    error_message = "L'etiquette calculee au plan doit deja etre correcte."
  }
}
```

## Proving a refusal: `expect_failures`

A serious module **refuses** invalid inputs. That behaviour is not asserted, since
nothing must be produced: it is **declared**.

```hcl
run "prefixe_trop_court_refuse" {
  command = plan

  variables {
    prefixe = "ab"
  }

  expect_failures = [var.prefixe]
}
```

The run passes **because** the validation rejected the value. Remove the module's
`validation`, and the same run fails, with an explicit message:

```text
Error: Missing expected failure

The checkable object, var.prefixe, was expected to report an error but did
not.
```

It is the only form that tests a module's **guard**. One useful caveat:
`expect_failures` only covers objects of the configuration under test, not those of
a child module.

## Chaining `run` blocks

The `run` blocks of a file execute **in sequence** and share their context. A `run`
can therefore prepare the ground for the next one, by executing **another**
configuration:

```hcl
run "prepare_le_prefixe" {
  module {
    source = "./prefixe"
  }
}

run "utilise_le_prefixe_prepare" {
  variables {
    prefixe = run.prepare_le_prefixe.valeur
  }

  assert {
    condition     = output.etiquette == "ATELIER"
    error_message = "L'etiquette doit reprendre le prefixe prepare."
  }
}
```

The `module` block of a `run` accepts only `source` and `version`: any other
argument is refused with `An argument named "..." is not expected here`. Outputs of
a previous run are read as `run.<name>.<output>`.

## What `terraform test` returns

The exit code is **0** if everything passes, **1** as soon as a run fails. That is
the only contract usable in continuous integration, and human output is no
substitute. To automate, read the **JSONL** stream:

```bash
terraform test -json
```

```json
{"type":"test_summary","test_summary":{"status":"pass","passed":4,"failed":0,"errored":0,"skipped":0}}
```

Event types are `version`, `test_abstract`, `test_file`, `test_run` and
`test_summary`. The `-verbose` option adds `test_state` for `apply` runs and
`test_plan` for `plan` ones.

## Two measured traps

A **`-filter` matching no file** produces no error at all:

```text
$ terraform test -filter=tests/inexistant.tftest.hcl
Success! 0 passed, 0 failed.
```

Exit code **0**. A CI that trusts that code alone can therefore be green having
tested nothing, and that is exactly what happens when a filter path changes.

Next, a **failed assertion** does not stop the file: the following `run` blocks
still execute. An **error**, on the other hand, turns them into `skip`:

```text
  run "defaut"... fail            ← false assertion, the file continues
  run "avec_suffixe"... pass

  run "defaut"... fail            ← reference error, the file stops
  run "avec_suffixe"... skip
```

## `init` is still needed, sometimes

On a standalone module, with no provider and no module call, `terraform test` works
without `init`. As soon as the configuration **calls a module** or declares a
**provider**, it must be installed first:

```text
Error: Module not installed

This module is not yet installed. Run "terraform init" to install all modules
required by this configuration.
```

## Your turn

You know where a suite lives, how to cover a default, an option and a refusal, and
how to read the result by machine. The challenge has you write the suite of a
complete module, and checks that it **detects** a regression: each behaviour is
broken in turn in a copy of the module, and your suite must fail.

```bash
dsoxlab run modules-test-module
dsoxlab check modules-test-module
dsoxlab hint modules-test-module
```

It runs **offline**, with no provider at all.

Target exam sub-objective: **4d** (test a module).

Reference: [testing a module](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/tester-module/)
