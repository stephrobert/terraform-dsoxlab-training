# Scenario: read the state without parsing it by hand

**Target exam objective: 1e (inspect and manipulate state).**

`terraform state show` produces a sheet meant for a human, and the official
documentation forbids extracting anything from it programmatically. The trap:
that sheet lies by omission (null attributes disappear) and by caution (sensitive
ones are redacted), so a `grep` on its output returns nothing where the value
does exist.

## Target capability

Reliably extract the address and attributes of a resource recorded in the state,
including when the value is sensitive or null, by querying `terraform show -json`
rather than the human output of `terraform state show`.

## Where the learner starts

`challenge/work` holds a complete, already written configuration that has never
been initialised nor applied:

- `main.tf`: supplied in full, not to be modified. It declares
  `random_password.api` (24 characters), `random_pet.env`, three
  `random_pet.replicas` instances created by `count = 3`, a
  `local_file.inventaire` derived from `random_pet.env` and a
  `data.local_file.relecture` data source.
- `outputs.tf`: five `output` blocks whose value is replaced by `???`, the only
  file to complete. Three holes require a value only the state holds, two an
  address whose exact shape comes from listing the state.
- No `.terraform/`, no `terraform.tfstate`, no `.terraform.lock.hcl`.

## Target state

1. A local state exists, with six resources in `mode: managed` and one in
   `mode: data`.
2. The `adresse_data` output carries the data source address as it appears in the
   state, `data.` prefix included.
3. The `adresse_replica` output carries the address of the **second**
   `random_pet.replicas` instance, index included: without an index the address
   designates no instance and is worth nothing.
4. The `empreinte_inventaire` output equals the `content_sha256` recorded for the
   data source, obtained by HCL reference and not copied over.
5. The `secret_api` output is marked `sensitive = true` and equals the generated
   password, which `state show` redacts and only the JSON renders readable.
6. The `attributs_masques` output is the sorted list of `random_pet.env`
   attributes that are `null` in the state, hence absent from the human sheet.
7. A new plan proposes no change at all.

## How it is proven

The pytest suite never opens a `.tf` file, and never reads the human output of
`terraform state show` to derive a value. It runs `terraform show -json` in
`challenge/work`: the per-`mode` count validates state 1, and the addresses found
in `values.root_module.resources[].address` validate 2 and 3.
`terraform output -json` supplies the five outputs, whose values are compared
with those read from the state for 4 and 5, `sensitive` flag included. For state
6, the test recomputes the list of null attributes of `random_pet.env` from the
JSON itself and requires equality, which rules out guessing. The
`sensitive_values` object of `random_password.api` confirms the redaction really
comes from Terraform.

The suite also proves, by execution, what the sheet hides and what the command
cannot do: an address without an index exits 1 on `No instance found for the
given address!`, the redacted password never appears in the sheet, the null
attributes are absent from it, `state show` rejects `-json` (exit 1), and
`state show` refreshes nothing (its output is unchanged after an out-of-band
modification, while `plan -detailed-exitcode` returns 2). Finally,
`terraform plan -detailed-exitcode` must exit 0 for state 7.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-show/
