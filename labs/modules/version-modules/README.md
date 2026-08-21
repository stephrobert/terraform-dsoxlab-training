# A tag names a version, it does not freeze it

Versioning a shared module decouples the **module's pace** from the **pace of the
projects** consuming it. The mechanism is simple: a commit, a tag, a reference on
the caller side. What is rarely taught is what that mechanism **does not
guarantee**: a Git tag moves, and nothing on the Terraform side remembers the
revision actually installed.

## The move: commit, tag, reference

On the library side, a published version is a **commit** marked by an
**annotated** tag:

```bash
git tag -a v1.0.0 -m "1.0.0: initial etiquette module"
```

On the consumer side, the reference goes in the source URL, after `?ref=`:

```hcl
module "etiquette" {
  source = "git::https://exemple.fr/infra/modules.git//etiquette?ref=v1.0.0"

  prefixe = "atelier"
}
```

Three pieces in that address: the **repository**, the **sub-directory** behind
`//`, and the **revision** behind `?ref=`. The order is not free, the
sub-directory comes before the query arguments.

## What `ref` accepts, and what happens without it

`ref` takes "any value supported by the `git checkout` command", so a **tag**, a
**branch** or a **SHA-1**. Its absence is not neutral:

```text
Downloading git::file:///.../depot-modules for plaque...
```

Without `ref`, Terraform clones the **default branch**. Measured on a local
library: after a new commit on `main`, a `terraform init -upgrade` on the consumer
brings the new code in without any version having been published. That is the
worst possible setting for a shared module, and it is the **default**.

## The fact that changes everything: a tag moves

The `v1.0.0` tag designates a commit, and that association is not carved in
stone. A `git tag -f` changes it:

```bash
git tag -f v1.0.0 -m "same version, other code"
```

On the consumer side, nothing moved in the configuration. A plain `terraform init`
changes nothing either, the installed copy being kept. But a `terraform init
-upgrade` brings back **different code under the same number**:

```text
Upgrading modules...
Downloading git::file:///.../depot-modules?ref=v1.0.0 for plaque...
```

```text
content: value = "plaque ${var.etiquette} revision 2"
```

The same `?ref=v1.0.0`, two different bodies of code, without a single warning.

## The only immutable reference: the SHA-1

Run the same experiment again, this time with the commit's SHA-1:

```hcl
source = "git::https://exemple.fr/infra/modules.git//etiquette?ref=72a7572e7a9ede8d490c7611e0455491655301fd"
```

After the tag has moved and an `init -upgrade`, the installed content is
**unchanged**. A SHA-1 designates content, not a name: it is the only reference
that cannot be redefined.

The practical rule that follows: the **tag** for environments that follow
published versions, the **SHA-1** for whatever must be reproducible to the byte,
an audit baseline or a frozen production foundation.

## What actually freezes your modules

A reflex inherited from providers misleads many people: the `.terraform.lock.hcl`
file locks **only** providers. No module version selection is recorded in it, and
a project without a provider does not even produce one. The revision actually
installed therefore depends solely on what you write in `source`.

## The `version` argument does not exist here

Copying a registry block and changing only the source is the most frequent
mistake on this topic:

```hcl
module "etiquette" {
  source  = "git::https://exemple.fr/infra/modules.git//etiquette?ref=v1.1.0"
  version = "1.1.0"
}
```

```text
Error: Invalid registry module source address

Failed to parse module registry address: a module registry source address
must have either three or four slash-separated components.

Terraform assumed that you intended a module registry source address because
you also set the argument "version", which applies only to registry modules.
```

The message spells out Terraform's reasoning: seeing `version`, it assumed a
**registry** address, and parsed it as such.

## SemVer: the number states the nature of the change

| Component | When to increment | Example |
| --- | --- | --- |
| **MAJOR** | breaking change | `1.1.0` → `2.0.0` |
| **MINOR** | backwards-compatible addition | `1.0.1` → `1.1.0` |
| **PATCH** | backwards-compatible fix | `1.0.0` → `1.0.1` |

The criterion is mechanical: any change that **forces the caller to modify its
`module` block** is major. Renaming a variable, removing one, making one
mandatory, renaming an output. Adding a variable **with** a `default` is minor,
precisely because the caller has nothing to change.

## What a reusable module must not impose

The documentation distinguishes two roles. "Reusable modules should constrain only
their **minimum** allowed versions", while "Root modules should use a `~>`
constraint to set both a lower and upper bound". The reason is measurable: a
module setting an upper bound propagates it to every consumer.

```text
- Finding hashicorp/local versions matching "~> 2.4.0, >= 2.9.0"...

Error: Failed to query available provider packages

Could not retrieve the list of available versions for provider
hashicorp/local: no available releases match the given constraints ~> 2.4.0,
>= 2.9.0
```

The module's and the root's constraints **intersect**. The module blocked a
project that needed a more recent version.

## Speeding up a clone: `depth`

On a module repository with a long history, `depth=1` noticeably reduces `init`
time:

```hcl
source = "git::https://exemple.fr/infra/modules.git//etiquette?ref=v1.1.0&depth=1"
```

Mind the measured trade-off: with `depth`, the revision is passed to `git clone
--branch`, which does **not** accept a raw SHA-1.

```text
fatal: Remote branch 72a7572e7a9ede8d490c7611e0455491655301fd not found
```

A `depth=1` and SHA-1 pinning are therefore incompatible.

## Your turn

You can publish a version, choose between tag and SHA-1, recognise what makes a
change major, and explain why `version` has no place on a Git source. The
challenge has you publish three versions of a module, then consume them from three
projects, each with its own reference form.

```bash
dsoxlab run modules-version-modules
dsoxlab check modules-version-modules
dsoxlab hint modules-version-modules
```

It runs **offline**: the library is a local Git repository.

Target exam sub-objective: **4c** (refactor and version a module).

Reference: [versioning your modules](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/versionner-modules/)
