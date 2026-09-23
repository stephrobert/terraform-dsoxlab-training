# Providers, resources and data sources: who owns what

A provider, a resource, a data source: three words learned on day one, whose
difference only becomes clear at the first misplaced `destroy`. This tutorial
makes it visible before that `destroy` happens.

## The provider is the driver

A **provider** is an executable Terraform downloads and runs as a subprocess. It
knows how to talk to a system: a cloud API, a filesystem, a database. Terraform
itself can do nothing on its own.

```hcl
terraform {
  required_providers {
    local = {
      source  = "hashicorp/local"
      version = "~> 2.5"
    }
  }
}
```

`source` names the organisation and the provider name. Without it, Terraform
**guesses** on its default registry: the configuration still applies, and is
reproducible nowhere.

The `~> 2.5` constraint is pessimistic: it accepts `2.9`, refuses `3.0`. The
major version is locked, patches stay available.

## The resource: Terraform owns it

A **`resource`** block commits Terraform to a full lifecycle. It creates the
object, modifies it, and **destroys** it on `destroy`.

```hcl
resource "local_file" "resume" {
  content  = "..."
  filename = "${path.module}/resume.txt"
}
```

That is a commitment, not a description. Declaring as a `resource` a file
somebody else wrote is granting yourself the right to delete it.

## The data source: Terraform only reads

A **`data`** block queries. It creates nothing, modifies nothing, and appears in
no `destroy`.

```hcl
data "local_file" "catalogue" {
  filename = "${path.module}/catalogue.txt"
}
```

Note it is the **same** provider and the **same** type, `local_file`. One word
changes, and two opposite lifecycles follow.

The state keeps track of both, but tells them apart without ambiguity:

```bash
terraform show -json | jq '.values.root_module.resources[] | {mode, address}'
```

```text
{"mode": "data",    "address": "data.local_file.catalogue"}
{"mode": "managed", "address": "local_file.resume"}
{"mode": "managed", "address": "random_pet.reference"}
```

## References, and the graph they build

The only difference in writing is a prefix:

| To | Syntax |
|---|---|
| a resource | `TYPE.NAME.ATTRIBUTE` — `random_pet.reference.id` |
| a data source | `data.TYPE.NAME.ATTRIBUTE` — `data.local_file.catalogue.content` |

And it is enough. Terraform builds its graph from the **references it finds in
expressions**: no reference, no edge, no guaranteed order. A hand-written
`depends_on` is almost always the symptom of a missing reference.

## A data source is re-read on every plan

That is the consequence people forget, and it is very concrete:

```bash
echo "reference-05  onduleur  6 kVA" >> catalogue.txt
terraform plan -detailed-exitcode ; echo $?   # 2
```

**No `.tf` moved**, and the plan is no longer empty. The data source was
resolved again, its value changed, and everything depending on it moved with it.

If the exit code is `0` here, it is not that data sources are not re-read: it is
that **nobody uses it**. A value that irrigates nothing is never seen.

<Aside type="caution" title="A trigger does not copy a file">
To make a resource depend on a file being read, prefer `content_sha1` over
`content`. The digest changes as soon as the file does, and you avoid copying
the whole content into the state, which is neither encrypted nor small.
</Aside>

## The `destroy`, and what it must not touch

```bash
terraform destroy -auto-approve
ls resume.txt      # gone, Terraform had created it
ls catalogue.txt   # intact, Terraform never owned it
```

That is the full demonstration. Write `resource` instead of `data`, and the
second `ls` fails: Terraform believed it owned a file it had never created, and
erased it.

## Over to you

You now know that a provider is declared with its source and a pessimistic
constraint, that a `resource` commits Terraform all the way to destruction, that
a `data` only reads, that the `data.` prefix is enough to build the graph, and
that a re-read data source can move a plan without a single `.tf` having
changed.

The challenge has you write both natures, then prove what a `destroy` takes and
what it spares.

```bash
dsoxlab run getting-started-providers-resources-data-sources
dsoxlab check getting-started-providers-resources-data-sources
dsoxlab hint getting-started-providers-resources-data-sources
```

Exam sub-objective covered: **2b** (data sources), leaning on **5b** (provider
configuration and versioning).

Reference: [Providers, resources and data sources](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/providers-resources-data-sources/)
