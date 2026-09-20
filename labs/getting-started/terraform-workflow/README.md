# The Terraform workflow: read a plan before applying it

`init`, `plan`, `apply`, `destroy`: four commands people recite. The workflow is
not that list. It fits in a single question, asked **before** touching
anything: among my resources, which ones will be modified in place, and which
ones will be **destroyed then recreated**?

The difference is not cosmetic. A replacement makes an existing object
disappear, with everything it carries: an IP address, a generated password, a
volume. And the output of `terraform plan` announces both cases **in the same
block of text**.

## The plan on screen is not the plan you apply

Here is the most common trap of the workflow:

```bash
terraform plan     # you read something
terraform apply    # Terraform RE-PLANS, and applies what it finds then
```

In between, the state may have been refreshed, a colleague may have applied, a
data source may have changed. Nothing guarantees that what runs is what you
read.

```bash
terraform plan -out=tfplan    # the plan is SAVED
terraform apply tfplan        # that plan, no re-plan, no confirmation
```

The produced file is binary and versioned: only the tool can read it back. Once
applied, it becomes **stale**, and Terraform refuses to replay it.

## The only reliable reading is JSON

```bash
terraform show -json tfplan > plan.json
```

Every `resource_changes` entry carries a `change.actions` field. There are only
a few possible values, and they do not blur into each other:

| Actions | Meaning |
|---|---|
| `["no-op"]` | nothing moves |
| `["update"]` | **update in place**: the same object, modified |
| `["create"]` | creation |
| `["delete"]` | destruction |
| `["delete", "create"]` | **replacement**: the object goes, another is born |
| `["create", "delete"]` | replacement too, with `create_before_destroy` |

The last two rows are the point to remember: **the order changes, the meaning
does not**. A test looking only for `["delete", "create"]` would miss half the
cases.

```bash
jq '.resource_changes[] | select(.change.actions != ["no-op"]) | {address, actions: .change.actions}' plan.json
```

## What forces a replacement

An attribute is **ForceNew** or it is not, and that is decided in the provider,
not in your code. A few measured examples:

```hcl
resource "terraform_data" "configuration" {
  input = var.etiquette          # update in place
}

resource "terraform_data" "jeton" {
  triggers_replace = [var.etiquette]   # replacement
}

resource "local_file" "rapport" {
  content = "etiquette : ${var.etiquette}\n"   # replacement
}
```

`local_file` is instructive: **everything** forces a replacement there, down to
the file permissions. The provider does not know how to modify, it knows how to
write.

The `keepers` of a `random_*` resource and the `triggers` of a `null_resource`
are in the same situation: they exist precisely to cause a replacement.

<Aside type="caution" title="A plan is read before, not after">
The trace of a replacement in the plan is visible once you know where to look:
the future identifier of the resource is **unknown** (`after_unknown`). An
object that does not exist yet cannot promise its identifier. Conversely, an
update in place keeps its own: it is the same object.
</Aside>

## Over to you

You now know that a plan you read is not a plan you apply until it is saved,
that its only reliable reading is the actions field in JSON, that a replacement
is written `delete`+`create` in any order, and that what forces a replacement is
decided in the provider.

The challenge has you produce that plan, classify it, and apply it as is.

```bash
dsoxlab run getting-started-terraform-workflow
dsoxlab check getting-started-terraform-workflow
dsoxlab hint getting-started-terraform-workflow
```

Exam sub-objective covered: **6d** (generate and read an execution plan).

Reference: [The Terraform workflow](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/workflow-terraform/)
