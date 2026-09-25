# What Terraform manages, and what it merely reads

One word separates the two kinds of block, and it decides everything:
`resource` creates and manages, `data` reads. Until you have seen a `destroy`
wipe the managed objects without touching what the data source was reading, you
believe a `data` block is a read-only resource.

This lab imposes both real consequences, and they are not symmetric.

## The proof fits in one state field

```console
$ terraform show -json | jq -r '.values.root_module.resources[] | "\(.mode)\t\(.address)"'
data     data.local_file.catalogue
managed  local_file.resume
managed  null_resource.sceau
managed  random_pet.empreinte
```

`mode` is not open to interpretation: a created block comes out as `managed`, a
reading block as `data`. That field, and not a reading of the `.tf` files, is
what the lab queries.

The reference changes with the kind, and the prefix is the only clue:

| Kind | Reference |
| --- | --- |
| `resource "local_file" "resume"` | `local_file.resume.filename` |
| `data "local_file" "catalogue"` | `data.local_file.catalogue.content` |

## First consequence: destroy does not touch what it did not create

```console
$ terraform destroy -auto-approve
$ ls resume.txt catalogue.txt
ls: cannot access 'resume.txt': No such file or directory
catalogue.txt
```

The managed file disappears, the one that was only read stays, **byte for
byte**. That is what makes a `data` block usable on a resource you do not own.

## Second consequence: a data source is re-read on every plan

That is the one you do not see coming. Without touching a line of HCL:

```console
$ terraform plan -detailed-exitcode ; echo $?
0
$ echo "revision=4" >> catalogue.txt
$ terraform plan -detailed-exitcode ; echo $?
2
```

A data source is not a cache. It is re-read on every plan, and whatever it feeds
moves with it. A `0` in that second case would mean the value read feeds nothing.

It is the most frequent cause of a plan that moves "by itself": somebody
changed, elsewhere, a piece of data the configuration reads.

## The dependency comes from the reference, never from a `depends_on`

```hcl
resource "null_resource" "sceau" {
  triggers = {
    empreinte = random_pet.empreinte.id
    catalogue = data.local_file.catalogue.content
  }
}
```

Two dependencies, zero `depends_on`. Terraform builds its graph from the
references it finds in expressions: quoting an attribute is enough, and it is the
form the documentation prefers.

Note that `random_pet.empreinte.id` only exists **after creation**. Referencing
it is the only way to obtain it: no hand-written value could guess it.

## The version constraint, and its two-component trap

```hcl
local = { source = "hashicorp/local", version = "~> 2.5" }
```

The pessimistic operator lets the **rightmost** component written float:

| Constraint | Accepts | Rejects |
| --- | --- | --- |
| `~> 2.5` | 2.9 | 3.0 |
| `~> 2.5.0` | 2.5.9 | 2.6.0 |

With two components it is therefore the **minor** that floats, which is not what
most people think they are writing.

## Over to you

```bash
dsoxlab run getting-started-providers-resources-data-sources
dsoxlab check getting-started-providers-resources-data-sources
dsoxlab hint getting-started-providers-resources-data-sources
```

It runs **offline**, on `local`, `null` and `random`, `local` providing both a
resource **and** a data source of the same name.

Seven tests. The last one runs the `destroy` in a **copy** of the directory, so
the lab stays replayable without reapplying everything.

Exam objective targeted: **2b**, supported by **5b**.

Reference: [providers, resources and data sources](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/providers-resources-data-sources/)
