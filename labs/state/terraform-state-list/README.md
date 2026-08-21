# `terraform state list`: the address is the identity in the state

`terraform state list` lists the **instances** Terraform manages, one per line,
as their **address**. That address is the only name an instance has in the state:
it is what `state show`, `state mv`, `state rm`, `import` and `-replace` all
require. This tutorial shows how to read it and how to filter; the challenge will
have you find addresses when all you know is the real identifier.

## Resource, instance, address

The distinction that explains everything else: a **resource** is what you
declare, an **instance** is what Terraform creates. A `resource` block with
`count = 3` is **one** resource and **three** instances, so three lines and three
addresses:

```bash
terraform state list
```

```text
data.local_file.lecture
local_file.rapport
random_pet.noeud[0]
random_pet.noeud[1]
random_pet.noeud[2]
random_pet.zone["eu-west"]
random_pet.zone["us-east"]
module.reseau.random_pet.sous_reseau["a"]
module.reseau.data.local_file.relecture
```

Four address shapes coexist here, and you need to be able to write them:

| Declaration | Address of one instance |
| --- | --- |
| plain resource | `local_file.rapport` |
| `count` | `random_pet.noeud[0]`, indexed by **position** |
| `for_each` | `random_pet.zone["eu-west"]`, indexed by **key**, quotes included |
| inside a module | `module.reseau.random_pet.sous_reseau["a"]` |
| data source | `data.local_file.lecture` |

## The output order is not alphabetical

The list is sorted by **module depth**, then alphabetically. Instances of the
root configuration therefore come **first**, those of modules **after**, from the
shallowest to the deepest. In the output above, `module.reseau.*` comes after
`random_pet.zone`, which a purely alphabetical sort would forbid. Worth knowing
when reading a long listing: the bottom of the list is the modularised part.

## Filtering: the command takes patterns, not just full names

The address argument is a **filter**, and it works by family. Three uses that are
often believed impossible:

```bash
terraform state list random_pet.noeud       # all 3 instances of the resource
terraform state list 'random_pet.noeud[0]'  # a single instance
terraform state list module.reseau          # everything inside the module
```

An address **without an index** therefore does not designate a single instance:
it returns **all** instances of the resource. And a **module** address is a
perfectly valid filter, which descends into nested modules. That is the most
useful filtering the command offers, and the one people wrongly replace with
`grep`.

Several addresses can be combined, and the output then follows the **order of the
arguments**, not the sorted order.

**Always quote brackets.** Under `zsh`, `terraform state list
random_pet.noeud[0]` fails before it even reaches Terraform, with
`no matches found`: brackets are a filename pattern. Single quotes settle it for
any indexed or keyed address.

## Searching by identifier with `-id`

When you know an object's real identifier but not its address, `-id` filters on
the value of the `id` attribute:

```bash
terraform state list -id=deep-foxhound
```

```text
random_pet.noeud[0]
```

This is the central move of the challenge: going from an identifier to an
address. `-id` combines with an address, and you then get the **intersection** of
both filters.

## The diagnostics, and the asymmetry that matters

An address that matches nothing produces an **error** and exit code **1**, with
four distinct messages depending on what is missing:

| Address given | Diagnostic |
| --- | --- |
| resource absent | `Unknown resource` |
| instance absent from an existing resource | `Unknown resource instance` |
| module absent | `Unknown module` |
| type alone, without a name | `Invalid address` |

An **`-id` with no match**, however, produces **no error**: empty output, exit
code **0**. That asymmetry decides how you script the command: an address filter
is tested on its exit code, an `-id` filter on whether the output is empty.

## Counting managed resources without getting it wrong

The recipe going around is `terraform state list | grep -v ^data | wc -l`. It is
wrong as soon as a module contains a data source, because that address starts
with `module.`, not with `data`. Counting is done on the machine output, by
filtering on the `mode` field and descending into modules:

```bash
terraform show -json | jq '[.values.root_module
  | .. | .resources? // empty | .[]
  | select(.mode == "managed")] | length'
```

A textbook case of the principle governing these labs: assert on **structured**
output, never on output meant for a human.

## Your turn

You can tell a resource from an instance, write the four address shapes, filter
by resource, by instance and by module, search by `-id`, and count managed
resources without being caught by a module's data source. The challenge publishes
three identifiers and asks you for the matching addresses, in a project mixing
`count`, `for_each` and a module.

```bash
dsoxlab run state-terraform-state-list
dsoxlab check state-terraform-state-list
dsoxlab hint state-terraform-state-list
```

Target exam objective: **1e** (inspect state), Associate level.

Reference: [terraform state list](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/terraform-state-list/)
