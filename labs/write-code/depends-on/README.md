# depends_on: the last resort, not the reflex

Terraform orders resources by itself, from the **references** you write.
`depends_on` is only for the handful of cases no reference can express. Adding it
for comfort, duplicating a reference that is already there, orders nothing more
and damages the plan. This tutorial shows where the line runs, on a **throwaway**
network/server example, before the challenge has you decide block by block.

Everything runs on the `local` and `null` providers, locally.

## A reference already creates a dependency

When a resource **references** another's attribute, Terraform infers the order.
Here, the server quotes the network's name:

```hcl
resource "local_file" "reseau" {
  filename = "reseau.txt"
  content  = "cidr 10.0.0.0/24"
}

resource "local_file" "serveur" {
  filename = "serveur.txt"
  content  = "rattache a : ${local_file.reseau.filename}"
}
```

The JSON plan exposes that dependency. The `configuration` section lists each
expression's references:

```bash
terraform plan -out=tfplan
terraform show -json tfplan | jq '.configuration.root_module.resources[] | select(.address=="local_file.serveur") | .expressions.content.references'
```

```json
["local_file.reseau.filename", "local_file.reseau"]
```

And `serveur` has **no** `depends_on`:

```json
"ABSENT"
```

The order is guaranteed all the same. Adding `depends_on = [local_file.reseau]`
here would change nothing about the order, but would make the plan more
conservative. That is the comfort `depends_on` never to write.

## A reference waits for the upstream to finish, not for a name

A false idea circulates: that a reference only waits for a value to be known, not
for the resource to be really available. That is inaccurate. **A reference waits
for the upstream to have finished being applied.**

The proof takes one example where the upstream is slow. The `base` waits two
seconds before writing a marker; the `app` reads it, and declares a dependency
through `triggers`:

```hcl
resource "null_resource" "base" {
  provisioner "local-exec" {
    command = "sleep 2 && echo pret > marqueur.txt"
  }
}

resource "null_resource" "app" {
  triggers = { base = null_resource.base.id }

  provisioner "local-exec" {
    command = "cat marqueur.txt"
  }
}
```

```bash
terraform apply
```

The apply succeeds. Had the reference only waited for a "known name",
`cat marqueur.txt` would have run before `base` wrote it, and would have failed.
The success proves the reference did wait for `base` to **finish**.

## When a reference is not enough: depends_on

There remain cases where a resource depends on another's **behaviour**, without
using any of its data. A service preparing state on disk, for instance, without
exposing a usable attribute. There, there is nothing to reference, and
`depends_on` becomes necessary:

```hcl
resource "null_resource" "service" {
  provisioner "local-exec" {
    command = "sleep 1 && touch pret.flag"
  }
}

resource "null_resource" "consommateur" {
  depends_on = [null_resource.service]

  provisioner "local-exec" {
    command = "test -f pret.flag"
  }
}
```

```bash
terraform apply
```

The apply succeeds: `pret.flag` exists when `consommateur` looks for it. Without
the `depends_on`, Terraform would launch both in parallel and the check would
fail, with not a single reference to order them.

The plan confirms the explicit dependency:

```bash
terraform show -json tfplan | jq '.configuration.root_module.resources[] | select(.address=="null_resource.consommateur") | .depends_on'
```

```json
["null_resource.service"]
```

## The criterion that settles it

The rule is not "might the resource start too early?" (a reference already
handles that), but:

> **Does the resource use any of the upstream's data in its arguments?**

- **Yes**: a reference is enough, and it is preferable. No `depends_on`.
- **No**, and the dependency exists anyway (behaviour, side effect): then, and
  only then, `depends_on`.

The documentation sums it up: "You should only use `depends_on` as a last resort
because it can cause Terraform to create more conservative plans that replace
more resources than necessary."

## An alternative: replace_triggered_by

When the need is not to order but to **replace** a resource as soon as another
changes, `depends_on` is not the right tool: `replace_triggered_by` is, inside
the `lifecycle` block. The subject is covered in
[the Terraform lifecycle block](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/lifecycle-terraform/).

## Over to you

You can now tell a dependency already expressed by a reference from a genuinely
hidden one. The challenge has you clean up a configuration mixing both: a
redundant `depends_on` to remove, a hard-coded path to replace with a reference,
and the only legitimate `depends_on` to add.

```bash
dsoxlab run write-code-depends-on
dsoxlab check write-code-depends-on
dsoxlab hint write-code-depends-on
```

Exam objective targeted: **2d** (Terraform Authoring and Operations
Professional).

Reference: [depends_on in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/depends-on/)
