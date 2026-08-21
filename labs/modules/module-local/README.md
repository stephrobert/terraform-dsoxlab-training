# A local module is read in place, it is not installed

A module whose `source` is a **relative path** is not installed: its files are
already on disk, and Terraform reads them **where they are**. That is what lets
several projects share one module without duplicating it, and it is also what
makes a very common reflex pointless, rerunning `init` after modifying that
module.

Terraform still has to consider your path **local**. The rule is strict, and an
absolute path does not qualify.

## The playground

Two independent workshops, one shared template:

```text
commun/gabarit/main.tf
atelier-nord/main.tf
atelier-sud/main.tf
```

The template produces a plate from a label:

```hcl
# commun/gabarit/main.tf
resource "local_file" "plaque" {
  filename = "${path.root}/plaques/${var.etiquette}.txt"
  content  = "plaque ${var.etiquette}\n"
}
```

Each workshop calls it by a **relative path**, with its own label:

```hcl
module "gabarit" {
  source = "../commun/gabarit"

  etiquette = "nord"
}
```

## What `init` does, and does not do

It **records** the module, it does not copy it:

```text
Initializing modules...
- gabarit in ../commun/gabarit
```

The proof is in the working directory. After `init`, `.terraform/modules/` holds
**a single file**:

```bash
ls -A .terraform/modules/
```

```text
modules.json
```

No folder at all. That `modules.json`, written by Terraform, says where each
module was found:

```json
[
  {
    "Key": "gabarit",
    "Source": "../commun/gabarit",
    "Dir": "../commun/gabarit"
  }
]
```

`Source` is what you wrote, `Dir` is what Terraform will read. For a relative
path, **both coincide**, and point outside the cache. The documentation puts it
this way: "Local paths are special in that they are not 'installed' in the same
sense that other sources are: the files are already present on local disk."

## One module, several projects

The second workshop reads **exactly the same folder**, with its own label and its
own state:

```bash
cd atelier-sud && terraform apply
terraform output -raw plaque
```

```text
./plaques/sud.txt
```

Two root projects, two separate states, **one module**: that is the whole point of
a relative path. Each consumes the template its own way without the other knowing.

## The pointless reflex: rerunning `init`

Modify the template, then **without rerunning `init`**, replan from a workshop:

```hcl
content = "plaque ${var.etiquette} (revision 2)\n"
```

```text
  # module.gabarit.local_file.plaque must be replaced
      ~ content = <<-EOT # forces replacement
```

```bash
terraform plan -detailed-exitcode; echo $?
```

```text
2
```

The change is seen **immediately**. There is **no cache to invalidate** for the
content of a local module: `init` only rereads the `source` field, so only a
change to that field justifies rerunning it.

## The deciding rule: `./` or `../`

Terraform does not guess that a path is local, it **recognises it by its prefix**.
The documentation is normative: "A local path **must** begin with either `./` or
`../`". Forget it, and the path heads for an entirely different mechanism:

```hcl
module "gabarit" {
  source = "commun/gabarit"
}
```

```text
Error: Invalid module source address

Terraform failed to determine your intended installation method for remote
module package "commun/gabarit".

If you intended this as a path relative to the current module, use
"./commun/gabarit" instead. The "./" prefix indicates that the address is a
```

The message hands you the fix. Without a prefix, Terraform looked for a **remote
package**.

## The misleading case: an absolute path

An absolute path does designate a folder present on disk. Terraform still does
**not** consider it local: "Terraform does not consider an absolute filesystem
path to be a local path. Instead, Terraform will treat that in a similar way as a
remote module and copy it into the local module cache."

The `init` says so plainly:

```text
Downloading file:///chemin/vers/commun/gabarit for gabarit...
- gabarit in .terraform/modules/gabarit
```

And `modules.json` records something else entirely:

```json
{
  "Key": "gabarit",
  "Source": "file:///chemin/vers/commun/gabarit",
  "Dir": ".terraform/modules/gabarit"
}
```

One nuance measured on 1.15.4 under Linux: that `Dir` is a **symbolic link** to
the source, not the deep copy the word "copy" suggests.

Two practical consequences. First, your configuration becomes **non-portable**:
the absolute path only exists on your machine. Second, and this is the costlier
trap, a module turned into a **package** can no longer reach anything **above
it**: if that module itself calls a sibling through `../autre`, the `init` fails.

```text
Error: Local module path escapes module package
```

## Your turn

You know a local module is not installed, that `modules.json` tells which folder
each call really reads, that a modification is seen without `init`, that the `./`
or `../` prefix is what defines a local path, and what an absolute path changes.
The challenge hands you three projects to wire onto one shared module, one of
which must serve as a counter-example.

```bash
dsoxlab run modules-module-local
dsoxlab check modules-module-local
dsoxlab hint modules-module-local
```

Target exam sub-objective: **4b** (use a module), Associate level.

Reference: [using a local module](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/module-local/)
