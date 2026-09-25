# The lifecycle block decides the order, not you

The `lifecycle` block reorders Terraform's dependency graph, propagates in a
counter-intuitive direction, and refuses some values people think legitimate.
This tutorial lays out its rules one by one on a **throwaway** example: a build
chain producing a versioned artefact. The challenge then has you apply those same
rules to another setting.

The proof of a behaviour is always read from the JSON plan's `actions` array:
`["delete", "create"]` is the default order, `["create", "delete"]` proves a rule
reversed it. Everything runs on `local`, `random` and `terraform_data`, with no
cloud.

## Setting up the example

In a separate directory, a `main.tf` with no `lifecycle` block at all, so as to
start from the default behaviour:

```hcl
variable "build" {
  type    = number
  default = 1
}

resource "random_pet" "empreinte" {
  length  = 2
  keepers = { build = var.build }
}

resource "local_file" "artefact" {
  filename = "${path.module}/out/artefact-${random_pet.empreinte.id}.txt"
  content  = "build=${var.build}\n"
}
```

The artefact's name depends on the fingerprint, so changing `build` forces a
**replacement**. After `init` and `apply`, look at the default order:

```bash
terraform plan -var 'build=2' -out=tf.plan
terraform show -json tf.plan | jq -c '.resource_changes[] | select(.address=="local_file.artefact") | .change.actions'
```

```text
["delete","create"]
```

Terraform **destroys before creating**. There is therefore a moment when the
artefact no longer exists.

## create_before_destroy: removing the outage window

Add a `lifecycle` block to the artefact:

```hcl
  lifecycle {
    create_before_destroy = true
  }
```

```bash
terraform apply -auto-approve
terraform plan -var 'build=2' -out=tf.plan
terraform show -json tf.plan | jq -c '.resource_changes[] | {a: .address, actions: .change.actions}'
```

```text
{"a":"local_file.artefact","actions":["create","delete"]}
{"a":"random_pet.empreinte","actions":["create","delete"]}
```

The artefact switches to `["create", "delete"]`: the window is gone. Look at the
second line, that is the central trap: `random_pet.empreinte` switched too,
although you wrote nothing on it. The rule propagates towards the resource's
**dependencies**, not towards its dependents. The artefact depends on the
fingerprint, so in order to create the new artefact first, the new fingerprint
must exist first. Had you put the rule on `random_pet.empreinte`, the artefact
would have stayed at `["delete", "create"]`.

## prevent_destroy: refusing a destructive plan

Add a protected resource:

```hcl
resource "local_file" "archive" {
  filename = "${path.module}/out/archive.txt"
  content  = "donnees a conserver"

  lifecycle {
    prevent_destroy = true
  }
}
```

```bash
terraform apply -auto-approve
terraform plan -destroy
```

```text
Error: Instance cannot be destroyed

  on main.tf line 15:
  15: resource "local_file" "archive" {
```

The plan fails before any action. Mind the limit, it is essential: that
protection only holds while the `resource` block exists. Delete the
`local_file.archive` lines, and Terraform will destroy the object without
protest, because the rule is not recorded in state. No block, no protection.

## ignore_changes: ignoring an attribute, not the resource

A resource one of whose attributes is driven elsewhere. Here, the content is
ignored while permissions stay under control:

```hcl
variable "note" {
  type    = string
  default = "v1"
}

variable "droits" {
  type    = string
  default = "0644"
}

resource "local_file" "config" {
  filename        = "${path.module}/out/config.txt"
  content         = var.note
  file_permission = var.droits

  lifecycle {
    ignore_changes = [content]
  }
}
```

Note the syntax: `[content]`, without quotes. Try both attributes:

```bash
terraform apply -auto-approve
terraform plan -var 'note=v2' -out=tf.plan
terraform show -json tf.plan | jq -c '.resource_changes[] | select(.address=="local_file.config") | .change.actions'
```

```text
["no-op"]
```

```bash
terraform plan -var 'droits=0600' -out=tf.plan
terraform show -json tf.plan | jq -c '.resource_changes[] | select(.address=="local_file.config") | .change.actions'
```

```text
["delete","create"]
```

The content change is absorbed (`no-op`), the permissions change goes through.
Had you written `ignore_changes = all`, that second plan would be empty too: you
would have blinded the whole resource. A deeper trap: `ignore_changes` compares
the **configuration with state**, not with the real file. Changing the file by
hand, outside Terraform, would not be absorbed.

## replace_triggered_by: replacing from a bare value

You want a resource replaced when `build` changes, without any of its attributes
moving. First reflex, point at the variable:

```hcl
lifecycle {
  replace_triggered_by = [var.build]
}
```

```bash
terraform validate
```

```text
Error: Invalid reference in replace_triggered_by expression
```

`replace_triggered_by` only accepts **managed resources**, never a variable nor a
local. The remedy is `terraform_data`, a built-in provider-less resource carrying
the value and becoming referenceable:

```hcl
resource "terraform_data" "jeton" {
  input = var.build
}

resource "local_file" "sceau" {
  filename = "${path.module}/out/sceau.txt"
  content  = "sceau"

  lifecycle {
    replace_triggered_by = [terraform_data.jeton]
  }
}
```

```bash
terraform apply -auto-approve
terraform plan -var 'build=2' -out=tf.plan
terraform show -json tf.plan | jq -c '.resource_changes[] | select(.address=="local_file.sceau") | {actions: .change.actions, reason: .action_reason}'
```

```text
{"actions":["delete","create"],"reason":"replace_by_triggers"}
```

`action_reason: "replace_by_triggers"` is the exact signature: it is the only
value proving a `replace_triggered_by`. Another one would betray a replacement
coming from an attribute change.

## precondition and postcondition

Two checks also live in the `lifecycle` block. The `precondition` verifies an
assumption **before** the action; the `postcondition` reads the result back
through `self` **after** it. On our artefact, you could require a strictly
positive build and a non-empty file:

```hcl
  lifecycle {
    create_before_destroy = true

    precondition {
      condition     = var.build > 0
      error_message = "build doit etre strictement positif."
    }

    postcondition {
      condition     = length(self.content) > 0
      error_message = "L'artefact ecrit est vide."
    }
  }
```

`self` only exists in a postcondition: it is the only mechanism able to read the
produced object back. The subject is explored in
[validating a Terraform configuration's inputs](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/conditions-terraform/).

## Over to you

You can now read a replacement's order and cause in the JSON plan. The challenge
applies these rules to another setting and checks every behaviour:

```bash
dsoxlab run write-code-lifecycle
dsoxlab check write-code-lifecycle
dsoxlab hint write-code-lifecycle
```

| Rule | Effect | The trap |
|---|---|---|
| `create_before_destroy` | create before destroying | propagates towards **dependencies** |
| `prevent_destroy` | rejects the destruction plan | bypassed by deleting the block |
| `ignore_changes` | ignores an attribute | compares config and state, not reality |
| `replace_triggered_by` | replaces when a target moves | refuses variables: go through `terraform_data` |
| `precondition` / `postcondition` | validate at plan time | `self` only in a postcondition |

Exam objective targeted: **2d** (Terraform Authoring and Operations
Professional).

Reference: [the Terraform lifecycle block](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/lifecycle-terraform/)
