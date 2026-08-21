# count, for_each and the positional-index trap

The **`count`** and **`for_each`** meta-arguments both create several instances
of a single resource. They look alike, but one detail separates them and causes
collateral destruction: `count` indexes instances by an **integer**, `for_each`
by a **key**. This tutorial shows the difference on a throwaway signs example,
the index-shift trap, the conditional `count`, and migrating `count` to
`for_each` without destroying anything. The challenge then makes you pick the
right meta-argument on a different case.

Proof always comes from the **JSON plan** (`terraform show -json`), never the
human output, which is read too fast.

## count: a number of copies, indexed by integer

`count = N` creates `N` identical instances, addressed `resource.name[0]`,
`resource.name[1]`, and so on. The current index is `count.index`, starting at
**0**:

```hcl
resource "local_file" "copy" {
  count    = 3
  filename = "${path.module}/copy-${count.index}.txt"
  content  = "item ${count.index}\n"
}
```

`count` needs a value **known before apply**: it cannot depend on an attribute
that only exists once the resource is created.

## for_each: one instance per key

`for_each` takes a **map** or a **set** and creates one instance per element,
addressed by its **key**: `resource.name["north"]`. Inside the block, `each.key`
is the current key and `each.value` its value:

```hcl
resource "local_file" "sign" {
  for_each = toset(["north", "south", "east"])
  filename = "${path.module}/sign-${each.key}.txt"
  content  = "zone ${each.key}\n"
}
```

A single block cannot carry both: `count` **and** `for_each` together raise
`Error: Invalid combination of "count" and "for_each"`.

## The trap: count's positional index

Here is the whole point. With `count`, an instance's identity is its
**position**. Remove an element from the **middle** of a list, and everything
after it **shifts by one**. Terraform does not see "an element disappeared", it
sees "the instance at this index changed its content".

```hcl
variable "zones" {
  type    = list(string)
  default = ["north", "south", "east"]
}

resource "local_file" "post" {
  count    = length(var.zones)
  filename = "${path.module}/post-${var.zones[count.index]}.txt"
  content  = "zone=${var.zones[count.index]}\n"
}
```

Apply with the three zones, then drop `south` (the middle one). The JSON plan is
unambiguous:

```json
{"address":"local_file.post[0]","actions":["no-op"]}
{"address":"local_file.post[1]","actions":["delete","create"]}
{"address":"local_file.post[2]","actions":["delete"]}
```

`post[1]` (which held `south`) is **destroyed and recreated** with `east`, and
`post[2]` is **destroyed**. Removing one zone recreated another. Harmless on a
file; an incident on a database or a volume.

## for_each does not have this trap

Same zones, keyed by name. Drop `south`: Terraform only touches `south`, because
identity is the **key**, not the position.

```json
{"address":"local_file.post[\"north\"]","actions":["no-op"]}
{"address":"local_file.post[\"south\"]","actions":["delete"]}
{"address":"local_file.post[\"east\"]","actions":["no-op"]}
```

Hence the official rule: `count` when instances are **interchangeable** (a number
of identical copies); `for_each` as soon as they have their **own identity** that
adding or removing one must not shift.

## Conditional count: 0 or 1 instance

The one truly common use of `count` is the **on/off**: a resource present or
absent depending on a boolean, with `count = condition ? 1 : 0`.

```hcl
resource "local_file" "banner" {
  count    = var.display ? 1 : 0
  filename = "${path.module}/banner.txt"
  content  = "promo\n"
}
```

At `false`, no instance exists. Going from 0 to 1 creates `banner[0]` and
**destroys nothing else**: the "count 0 to 1 destroys the others" claim is a
myth. To expose the attribute of a 0-or-1 resource, the splat `banner[*].id` has
length 0 or 1, and **`one()`** reduces it to a single value, or `null` if empty:

```hcl
output "banner_id" {
  value = one(local_file.banner[*].id)
}
```

## Migrating count to for_each without destroying

This is what separates beginner from professional use. Change a `count` block to
`for_each` **without care** and you destroy and recreate everything: addresses go
from `post[0]` to `post["north"]`, and Terraform cannot guess the mapping. A
**`moved`** block gives it:

```hcl
moved {
  from = local_file.post[0]
  to   = local_file.post["north"]
}
```

The plan becomes **entirely no-op**, and each address change is traced in the
JSON by `previous_address`. A simpler case is handled **automatically** by recent
versions: adding `count = 1` to a resource that had none migrates `post` to
`post[0]` with no destruction. But as soon as **keys** must be guessed, as with
`for_each`, the `moved` block is mandatory.

## Your turn

You know that `count` indexes by integer and `for_each` by key, that count's
index shift recreates the following instances, that `count = cond ? 1 : 0` with
`one()` handles the optional case, and that `moved` migrates without destroying.

```bash
dsoxlab run write-code-count
dsoxlab check write-code-count
dsoxlab hint write-code-count
```

Exam objectives: **4b** (Terraform Associate, meta-arguments) and the
Professional `moved` migration.

Reference: [count and for_each in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/count-terraform/)
