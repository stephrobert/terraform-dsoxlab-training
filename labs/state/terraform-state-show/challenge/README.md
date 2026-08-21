# 🎯 Challenge: extract from the state what the human sheet refuses to show

## ✅ Objective

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

## 🔍 Validation

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
- `terraform state show` has no `-json` option (exit code 1) and **refreshes
  nothing**: after a change made outside Terraform its output is unchanged while
  `plan -detailed-exitcode` returns 2;
- `plan -detailed-exitcode` returns 0 at the end: filling in outputs changes
  nothing in the infrastructure.

Stuck? `dsoxlab hint state-terraform-state-show`.
