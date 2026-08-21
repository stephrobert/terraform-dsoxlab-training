# The standard module structure, and the one file name that matters

Terraform loads **every** `.tf` file in a directory and treats them as a single
document. Splitting into `main.tf`, `variables.tf` and `outputs.tf` therefore
changes nothing about the result: it is a **reading** convention.

Except for one family of names, `override.tf` and `*_override.tf`, which
Terraform loads **last** and which **override** what came before. This tutorial
shows the layout the ecosystem expects, then that exception, measured.

## What the documentation calls the Standard Module Structure

It exists, it has an official page, and tooling relies on it: "We recommend a
common repository structure [...] Terraform tooling is built to understand the
standard module structure and use that structure to generate documentation,
index modules for the module registry, and more."

The official minimal layout is **four files**:

```text
minimal-module/
├── README.md
├── main.tf
├── variables.tf
└── outputs.tf
```

Three remarks that are often missed:

- **`README.md` is part of the minimum**, not of the options. And it does not
  have to document inputs and outputs: "The README doesn't need to document
  inputs or outputs of the module because tooling will automatically generate
  this."
- **`LICENSE` sits at the same level**: "many organizations will not adopt a
  module unless a clear license is present. We recommend always having a license
  file, even if it is not an open source license."
- The `terraform` block is **not** part of that layout. The style guide gives it
  its own file: "A `terraform.tf` file that contains a single `terraform` block
  which defines your `required_version` and `required_providers`".

## Nested modules, and calling them by relative path

A module can hold others, under `modules/`. The documentation attaches a
visibility rule to the **README**:

> Any nested module with a `README.md` is considered usable by an external user.
> If a README doesn't exist, it is considered for internal use only.

A nested module without a README is therefore **internal**, and that distinction
is written nowhere else than in the presence of the file.

The call uses a **relative path**:

```hcl
module "carte" {
  source   = "./modules/carte"
  for_each = var.zones

  zone = each.key
}
```

The reason is technical: "they should use relative paths like
`./modules/consul-cluster` so that Terraform will consider them to be part of the
same repository or package, rather than downloading them again separately". The
plan JSON lets you check it:

```bash
terraform plan -out=p.tfplan
terraform show -json p.tfplan | jq '.configuration.root_module.module_calls.carte.source'
```

```json
"./modules/carte"
```

## The `examples/` directory

The docs expect standalone examples: "Examples of using the module should exist
under the `examples/` subdirectory at the root of the repository." They validate
independently of the root:

```bash
terraform -chdir=examples/minimal init
terraform -chdir=examples/minimal validate -json
```

```json
{"valid": true, "error_count": 0}
```

One detail matters for a published module: inside an example, "any `module`
blocks should have their `source` set to the address an external caller would
use, not to a relative path", since those examples end up copied elsewhere.

## A `type` on every output

The 1.15 style guide aligns outputs with variables: "Like you would for
variables, provide a `type` and `description` for each output", in the order
`Type, Description, Value, Sensitive`.

```hcl
output "emplacements" {
  type        = map(string)
  description = "Chemin de la carte, par zone."
  value       = { for nom, instance in module.carte : nom => instance.emplacement }
}
```

The declared type shows up as such in machine output:

```bash
terraform output -json | jq '.emplacements.type'
```

```json
["map", "string"]
```

Drop the `type` line and the same value comes back as
`["object", {"nord": "string", "sud": "string"}]`: the inferred type, key by key.

## The exception: `override.tf`

Here is the only place where the **file name** changes the result. Take a
resource declared in `main.tf`:

```hcl
resource "local_file" "registre" {
  filename        = "${path.root}/registre.txt"
  content         = "registre des cartes\n"
  file_permission = "0644"
}
```

Add an `override.tf` that **redeclares the same resource**, with a single
attribute:

```hcl
resource "local_file" "registre" {
  file_permission = "0600"
}
```

Terraform **merges** both, and the second wins:

```bash
terraform apply -auto-approve
terraform show -json | jq '.values.root_module.resources[]
  | select(.address == "local_file.registre") | .values.file_permission'
```

```json
"0600"
```

The file on disk does carry `600`. The documentation puts it this way: "Terraform
loads this and all files ending with `_override.tf` last."

**Change the file name and everything collapses.** The same content in a
`surcharge.tf` produces:

```text
Error: Duplicate resource "local_file" configuration

  on surcharge.tf line 1:
   1: resource "local_file" "registre" {

A local_file resource named "registre" was already declared at
main.tf:8,1-33. Resource names must be unique per type in each module.
```

That is the demonstration in one command: file names are cosmetic, **except
those**. The documentation does warn against their casual use, because they make
a configuration hard to read: keep them for cases where you cannot modify the
original file.

## Your turn

You know what the standard structure holds, why a nested module's `README`
decides its visibility, why the call uses a relative path, what a `type` on an
output changes in machine output, and what is special about `override.tf`. The
challenge hands you a single file with everything piled up, to split cleanly.

```bash
dsoxlab run modules-module-structure
dsoxlab check modules-module-structure
dsoxlab hint modules-module-structure
```

Target exam sub-objective: **4a** (write and use modules), Associate and
Professional level.

Reference: [standard module structure](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/structure-module/)
