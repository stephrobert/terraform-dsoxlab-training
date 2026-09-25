# 🎯 Challenge: four resources, four operations

## Starting point

`challenge/work` holds four `resource {}` blocks and two `output` blocks, all
holed with `???`. `versions.tf` and `variables.tf` are **complete, not to be
modified**: they declare the variables `etiquette` (string) and `generation`
(number).

The `???` are syntax errors: `terraform init` fails as it stands. Every hole
carries above it a comment stating what is expected.

## ✅ Objective

Wire the configuration so that state holds exactly four managed resources, at
addresses `random_pet.hote`, `local_file.fiche`, `terraform_data.sceau`,
`local_file.journal`:

1. **`random_pet.hote`** carries `keepers` tied to `var.generation`: a change of
   generation must replace it.

2. **`local_file.fiche`** draws the host's id into its `filename` (an
   **implicit** dependency, with no `depends_on`), and carries
   `create_before_destroy = true`.

3. **`terraform_data.sceau`** carries `input = var.etiquette` (an in-place update
   when the label changes) and `triggers_replace` holding the host's id (a
   replacement when it changes).

4. **`local_file.journal`** depends on the seal through `depends_on` **alone**,
   referencing none of its data: that is a behavioural dependency.

5. The outputs expose the fiche's path and the seal's `output` attribute.

After your `apply`, `terraform plan` must propose nothing.

## 🧭 What the tests read

The JSON plan's `resource_changes[].actions` array. The tests check the
signatures of the four operations:

- `etiquette=v2`: the seal must be at **`["update"]`** (in-place update).
- `generation=2`: the fiche must be at **`["create", "delete"]`**
  (`create_before_destroy`), not `["delete", "create"]`.

Badly wired blocks do not produce those signatures.

## 🔍 Validation

```bash
dsoxlab check write-code-declare-resources
```

Seven tests. They decode `terraform show -json` (state and configuration),
`output -json` and the JSON plan. None reads your `.tf`.
