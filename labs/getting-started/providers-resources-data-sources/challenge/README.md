# 🎯 Challenge: decide, for each block, whether it creates or reads

## 📦 Starting point

`challenge/work` holds `catalogue.txt`, **already on disk**: Terraform never
created it.

| File | State |
| --- | --- |
| `catalogue.txt` | supplied, **not to be modified** |
| `versions.tf` | the `required_providers` block is empty |
| `main.tf` | four blocks whose **kind** is a `???` |
| `outputs.tf` | two outputs to write |

`terraform init` fails as it stands: it does not know which providers to install.

## ✅ Objective

1. **Declare the three providers** (`local`, `null`, `random`) with a
   **pessimistic** version constraint.
2. **Choose each block's kind**: the one reading `catalogue.txt`, and those
   creating.
3. **Reference rather than copy**: the written file derives from the catalogue's
   contents, and the seal's `triggers` carries **both** the drawn value and what
   was read.
4. **Two outputs**, of two different kinds.

After your `apply`, `terraform plan` must propose nothing.

## 🧭 The word that decides everything

`resource` **creates and manages**. `data` **reads**. And the reference changes
with the kind:

```hcl
local_file.resume.filename              # a resource
data.local_file.catalogue.content       # a data source
```

Two consequences the tests check:

- **a data source creates nothing**, so `destroy` does not take it. If
  `catalogue.txt` disappears, a `resource` block was managing it;
- **it is re-read on every plan**. Changing `catalogue.txt` without touching a
  single `.tf` must move `plan -detailed-exitcode` from 0 to **2**. If it stays
  at 0, the value read feeds nothing.

## ⚠️ Two values you cannot write by hand

`random_pet.empreinte.id` only exists **after creation**. And the catalogue's
contents must come from the data source, not from a copy: otherwise it will not
follow when the file changes.

## 🔍 Validation

```bash
dsoxlab check getting-started-providers-resources-data-sources
```

Seven tests. None reads your `.tf`: the central proof is the `mode` field of
`terraform show -json`, which is `managed` or `data` without ambiguity.

The last one runs the `destroy` in a **copy** of the directory, so the lab stays
replayable.

Stuck? `dsoxlab hint getting-started-providers-resources-data-sources`.
