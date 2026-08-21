# Diagnose a drift, adopt an orphan

Two different situations lead to the same symptom, a plan proposing changes when
nobody touched the code. In the first, **the real object changed** outside
Terraform: that is a **drift**. In the second, an object exists but **was never
in the state**: that is an **orphan**.

Each is repaired with different tools, and confusing them is costly: you do not
fix a drift with an `import`, and you do not recover an orphan with a `refresh`.

## The playground

In a directory of its own, outside the challenge:

```hcl
terraform {
  required_version = ">= 1.7"
  required_providers {
    local  = { source = "hashicorp/local", version = ">= 2.5" }
    random = { source = "hashicorp/random", version = ">= 3.6" }
  }
}

resource "local_file" "bulletin" {
  filename = "${path.root}/sortie/bulletin.txt"
  content  = "bulletin du jour\n"
}
```

A `terraform init` then a `terraform apply` create the file. Now simulate the
incident everyone has already lived through, a fix applied straight on the
server:

```bash
echo "corrige a la main" > sortie/bulletin.txt
```

## An ordinary plan mixes two pieces of information

Terraform wants to recreate the file. That is correct, but not enough for a
diagnosis: the plan does not say whether the problem comes from the **real
world** moving or the **code** changing. The JSON shows it, the information is
stored **twice**:

```bash
terraform plan -out=ordinaire.tfplan
terraform show -json ordinaire.tfplan | jq '{
  drift: [.resource_drift[]?.address],
  changes: [.resource_changes[]?.address]
}'
```

```json
{
  "drift": ["local_file.bulletin"],
  "changes": ["local_file.bulletin"]
}
```

## `plan -refresh-only` isolates the drift

Refresh-only mode proposes no infrastructure change at all: it only describes
the **state catching up**. The difference reads in the JSON, where
`resource_changes` is now **empty**:

```bash
terraform plan -refresh-only -out=derive.tfplan
terraform show -json derive.tfplan > derive-plan.json
jq '{drift: [.resource_drift[]?.address], changes: [.resource_changes[]?.address]}' derive-plan.json
```

```json
{
  "drift": ["local_file.bulletin"],
  "changes": []
}
```

**That absence is the signature of the diagnosis.** Since a plan file is a
**binary**, converting it to JSON is not cosmetic: it is what makes the drift
readable in review, archivable, and checkable by a script.

## Two exit codes that do not say the same thing

`-detailed-exitcode` returns **0** with no change, **2** with changes, **1** on
error. Applied to both forms of plan, it becomes a diagnostic tool in its own
right:

| Command | What exit code 2 means |
| --- | --- |
| `terraform plan -detailed-exitcode` | the **real world** does not match the **code** |
| `terraform plan -refresh-only -detailed-exitcode` | the **state** does not match the **real world** |

This is the distinction most often missed. After a
`terraform apply -refresh-only`, which **writes the drift into the state**,
refresh-only returns **0** while the ordinary plan still returns **2**: the state
now tells the truth, but that truth still does not match the code. An ordinary
`apply` then brings the object back in line, and both codes drop to **0**
together.

## Adopting a resource that was never managed

The **`import` block**, declarative since Terraform **1.5**, attaches an existing
object to a state address. Two attributes are enough, the target address and the
object identifier at the provider:

```hcl
resource "random_string" "credential" {
  length = 22
}

import {
  to = random_string.credential
  id = "V3ryS3cretL3gacyStr1ng"
}
```

The plan announces the adoption, and the counter carries a category of its own,
`to import`:

```text
  # random_string.credential will be imported
Plan: 1 to import, 0 to add, 0 to change, 0 to destroy.
```

In JSON, the entry carries `"actions": ["no-op"]` and an `importing` field:
nothing is created or destroyed, the object simply changes status.

## The import trap: attributes that do not match

Here is what turns an adoption into a loss. If the **configuration** describes
attributes the imported object **does not carry**, Terraform does not merely
adopt, it **replaces**. Declare `length = 32` for a 22-character string:

```text
  # random_string.credential must be replaced
  # (imported from "V3ryS3cretL3gacyStr1ng")
  # Warning: this will destroy the imported resource
      ~ length      = 22 -> 32 # forces replacement
      ~ result      = "V3ryS3cretL3gacyStr1ng" -> (known after apply)
Plan: 1 to import, 1 to add, 0 to change, 1 to destroy.
```

The warning is explicit, **`this will destroy the imported resource`**, and the
JSON confirms it with `"actions": ["delete", "create"]` and
`"replace_paths": [["length"]]`. But it only appears **in the plan**: an
`apply -auto-approve` run without reading takes the value away, and the **next**
plan calmly reports `No changes`. The loss then becomes undetectable.

When the inherited value must survive as is, the guard rail is `ignore_changes`:

```hcl
resource "random_string" "credential" {
  length = 32

  lifecycle {
    ignore_changes = all
  }
}
```

The object is adopted **as it stands**, without Terraform trying to align it on a
configuration written for the objects to come.

## Which one, and when

| Symptom | Diagnosis | Repair |
| --- | --- | --- |
| The plan wants to recreate an existing object | drift, or orphan | `plan -refresh-only` to decide |
| `resource_drift` is not empty | **drift**: the real world changed | `apply -refresh-only`, then `apply` |
| The object is in no state at all | **orphan** | `import` block |
| The import announces `must be replaced` | diverging attributes | `ignore_changes`, or align the code |

## Your turn

You can isolate a drift with a refresh-only plan, read the difference between
`resource_drift` and `resource_changes`, tell apart what the two
`-detailed-exitcode` say, adopt a pre-existing resource with an `import` block,
and recognise in the plan the adoption about to destroy what it claims to take
over. The challenge hands you a file fixed by hand and an inherited token a third
party knows about, therefore impossible to regenerate.

```bash
dsoxlab run state-diagnose-state
dsoxlab check state-diagnose-state
dsoxlab hint state-diagnose-state
```

Target exam sub-objective: **1e** (manage state), Associate and Professional
level.

Reference: [diagnose the state](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/diagnostiquer-state/)
