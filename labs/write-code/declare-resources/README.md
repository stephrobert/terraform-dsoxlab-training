# A resource's lifecycle is read in the plan

Declaring a `resource {}` block is trivial. Saying, **before** applying, whether
Terraform will update the resource in place or destroy it to recreate it, is not.
Yet that is what the exam asks about, and what avoids bad surprises in
production. The answer is always in the plan, in JSON format.

This tutorial builds a **throwaway** example, a versioned artefact, and reads its
four lifecycle operations from the `resource_changes[].actions` array. Everything
runs on `local`, `random` and the built-in `terraform_data` resource, with no
cloud.

## The four operations, and their signature

Terraform only does four things to a resource, and each has a signature in the
JSON plan:

| Operation | `actions` in the plan |
|---|---|
| Create | `["create"]` |
| Update **in place** | `["update"]` |
| Replace (destroy then create) | `["delete", "create"]` |
| Destroy | `["delete"]` |

A fifth value, `["no-op"]`, signals there is nothing to do. The whole subject
comes down to telling an **in-place update** from a **replacement**: one is
painless, the other rebuilds the object.

## Setting up the example

In a separate directory, three resources and two variables:

```hcl
variable "niveau" {
  type    = string
  default = "beta"
}

variable "cycle" {
  type    = number
  default = 1
}

resource "random_pet" "serie" {
  length  = 2
  keepers = { cycle = var.cycle }
}

resource "local_file" "paquet" {
  filename = "${path.module}/out/paquet-${random_pet.serie.id}.txt"
  content  = "serie=${random_pet.serie.id}\n"

  lifecycle {
    create_before_destroy = true
  }
}

resource "terraform_data" "jeton" {
  input            = var.niveau
  triggers_replace = random_pet.serie.id
}
```

Two points of vocabulary. The type + name pair (`terraform_data.jeton`) is the
resource's **address** in state: renaming it amounts to destroying then
recreating the object, barring a `moved` block. And **`terraform_data`** belongs
to no provider: it is a built-in resource offering the full lifecycle (`input`,
`triggers_replace`, the computed `output` attribute).

After `terraform init` and `terraform apply`, an empty plan proposes nothing:

```bash
terraform plan -out=tfplan
terraform show -json tfplan | jq -c '[.resource_changes[] | {a: .address, ops: .change.actions}]'
```

```json
[{"a":"local_file.paquet","ops":["no-op"]},{"a":"random_pet.serie","ops":["no-op"]},{"a":"terraform_data.jeton","ops":["no-op"]}]
```

## Updating in place

Change the **level**. The token's `input` argument changes, but nothing requires
recreating the resource: Terraform updates it in place.

```bash
terraform plan -var 'niveau=stable' -out=tfplan
terraform show -json tfplan | jq -c '.resource_changes[] | select(.address=="terraform_data.jeton") | .change.actions'
```

```text
["update"]
```

`["update"]`: the object is modified, not recreated. It is the least expensive
case, and often the expected result.

## Replacing, and the order of the replacement

Now change the **cycle**. `random_pet.serie`'s `keepers` depend on it, so the
series is **replaced**, its id changes, and the effect propagates.

```bash
terraform plan -var 'cycle=2' -out=tfplan
terraform show -json tfplan | jq -c '.resource_changes[] | {a: .address, ops: .change.actions}'
```

```json
{"a":"random_pet.serie","ops":["create","delete"]}
{"a":"local_file.paquet","ops":["create","delete"]}
{"a":"terraform_data.jeton","ops":["delete","create"]}
```

Three replacements, but **two different orders**, and that is the whole point:

- `local_file.paquet` carries `create_before_destroy`, hence
  `["create", "delete"]`: the new file exists before the old one leaves, with no
  gap;
- `random_pet.serie`, which the package depends on, **inherits** the rule by
  propagation: it too switches to `["create", "delete"]`, although nothing is
  written on it;
- `terraform_data.jeton`, which is nobody's dependency carrying the rule, keeps
  the default order `["delete", "create"]`: it destroys before creating.

It is `triggers_replace` that triggered the token's replacement: it holds the
series' id, which has just changed.

## Destroying

A destruction plan shows the last operation:

```bash
terraform plan -destroy -out=tfplan
terraform show -json tfplan | jq -c '.resource_changes[] | select(.address=="local_file.paquet") | .change.actions'
```

```text
["delete"]
```

## Over to you

You can now read from the plan whether a resource will be updated, replaced or
destroyed. The challenge has you build a configuration where those operations
fire on demand, and the tests check every signature.

```bash
dsoxlab run write-code-declare-resources
dsoxlab check write-code-declare-resources
dsoxlab hint write-code-declare-resources
```

Exam objective targeted: **1c** (Terraform Authoring and Operations
Professional).

Reference: [declaring Terraform resources](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/declarer-ressources/)
