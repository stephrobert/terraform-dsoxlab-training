# Read the state without parsing it by hand

## The situation

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

Reference: https://www.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-show/ (in French)

## 🎯 Challenge: extract from the state what the human sheet refuses to show

### ✅ Objective

In `challenge/work`, `main.tf` and `versions.tf` are **complete and must not be
modified**. The only file to fill in is **`outputs.tf`**, which carries five
`???`.

Apply first, otherwise there is nothing to inspect:

```bash
terraform init
terraform apply
```

Then fill in the five outputs:

1. **`adresse_data`**: the address of the data source, as the state carries it.
   Mind the prefix.
2. **`adresse_replica`**: the address of the **second** instance of
   `random_pet.replicas`. Without an index, `terraform state show` refuses the
   address.
3. **`empreinte_inventaire`**: the **SHA-256** checksum of the file read by the
   data source. An **HCL reference**, not a copied value.
4. **`secret_api`**: the generated password. Terraform will refuse the output
   until it is declared sensitive, and the `state show` sheet will not show it to
   you.
5. **`attributs_masques`**: the **sorted** list of `random_pet.env` attributes
   that are `null` in the state. `terraform state show` does not display them at
   all.

Two commands are enough, and they are not equivalent:

```bash
terraform state show random_pet.env      # the sheet, for your eyes
terraform show -json | jq '.values...'   # the document, for a script
```

### 🔍 Validation

`dsoxlab check state-terraform-state-show` **recomputes every truth** from
`terraform show -json` and never uses the output of `state show` to derive a
value. It only runs it to prove what it **hides**.

Proven by execution:

- the state holds **six** resources in `mode: managed` and **one** in
  `mode: data`;
- both your addresses really exist in the state, index included, and an address
  **without** an index fails with exit code 1 on
  `No instance found for the given address!`;
- `secret_api` does carry `sensitive = true` and equals the state's password,
  which the sheet redacts as `(sensitive value)` and `sensitive_values` flags;
- your list of hidden attributes is compared with the one the test **recomputes**
  from the JSON, and the test checks they are indeed absent from the sheet;
- `terraform state show` and `-json`: the test reads your **version** instead of
  assuming it. Up to 1.15 the flag does not exist and the command exits with 1;
  since 1.16 it exists and returns one resource, where `show -json` returns the
  whole state. What does not change is the scope of each;
- `terraform state show` **refreshes nothing**: after a change made outside
  Terraform, its output is unchanged while `plan -detailed-exitcode` returns 2;
- `plan -detailed-exitcode` returns 0 at the end: filling in outputs changes
  nothing in the infrastructure.

Stuck? `dsoxlab hint state-terraform-state-show`.
