# Add an instance without destroying the others

`for_each`'s real subject is not its syntax, it is what it **avoids**. With
`count`, inserting an entry in the middle of a list shifts every following index,
and Terraform destroys then recreates resources that had no reason to move. In
production, that is an outage.

This tutorial teaches the mechanism on a **throwaway** example: a handful of log
buckets. The challenge then has you migrate another setting from `count` to
`for_each` without breaking anything. The lab runs on `random`, with no cloud.

## Prerequisites

- `terraform` on the PATH, version **1.1 or later** (`moved` blocks do not exist
  before that).
- Network access for the first `terraform init`.

## Why count is fragile

`count` addresses instances by **position**: `[0]`, `[1]`, `[2]`. That position
has no business meaning, it depends solely on the list's order. Set up two
buckets:

```hcl
variable "buckets" {
  type    = list(string)
  default = ["app", "audit"]
}

resource "random_pet" "bucket" {
  count  = length(var.buckets)
  length = 2
}
```

After the `apply`, state names them by rank:

```bash
terraform state list
```

```text
random_pet.bucket[0]
random_pet.bucket[1]
```

Insert a bucket in first position and everything slides: what was `[0]` becomes
`[1]`, what was `[1]` becomes `[2]`. Terraform does not see a shift, it sees that
instance `[0]` must now carry different values. It **modifies or replaces** it,
in cascade.

## for_each addresses by key

`for_each` replaces position with a **stable key**. The `app` instance is called
`["app"]`, and will keep that name whatever its place in the list:

```hcl
resource "random_pet" "bucket" {
  for_each = toset(var.buckets)
  length   = 2
}
```

Two constraints Terraform imposes:

- `for_each` accepts a **map** or a **set of strings**, never a list. Hence the
  `toset()`.
- The keys must be **known at plan time**. A key derived from an attribute of a
  resource not yet created makes the plan fail.

Inside the resource body, `count.index` gives way to `each.key` and `each.value`.

## Migrating without destroying: moved blocks

Going from `count` to `for_each` changes the instances' **address** in state.
With nothing else, Terraform concludes the old addresses are gone and new ones
appear: it destroys and recreates everything. The `moved` block declares the
re-addressing:

```hcl
moved {
  from = random_pet.bucket[0]
  to   = random_pet.bucket["app"]
}

moved {
  from = random_pet.bucket[1]
  to   = random_pet.bucket["audit"]
}
```

Three properties make it the right method, preferable to `terraform state mv`:

- it is **versioned** with the code and seen in code review,
- it is **replayed automatically** by the whole team and by CI,
- it is **declarative**: nobody has to remember to run a command.

The official documentation recommends **keeping** `moved` blocks: removing them
is a breaking change for anyone who has not applied yet.

## Reading the proof in the JSON plan

A successful re-addressing shows in the plan, and that is what the tests check:

```bash
terraform plan -out=tfplan
terraform show -json tfplan | jq -c '.resource_changes[] | {address, previous_address, actions: .change.actions}'
```

```text
{"address":"random_pet.bucket[\"app\"]","previous_address":"random_pet.bucket[0]","actions":["no-op"]}
{"address":"random_pet.bucket[\"audit\"]","previous_address":"random_pet.bucket[1]","actions":["no-op"]}
```

Two signatures to know:

- `"actions": ["no-op"]` together with a **`previous_address`**: the resource
  changed address without being touched. That is the desired outcome.
- `"actions": ["delete", "create"]`: the resource is **replaced**. The
  re-addressing failed.

## The misleading splat on for_each

One last trap, which appears in many tutorials, often badly described. The splat
syntax `resource[*].attribute` is designed for **lists**. On a resource driven by
`for_each`, which is a **map**, it nonetheless raises no error: it silently wraps
the map in a single-element array.

```bash
echo 'random_pet.bucket[*]' | terraform console
```

```text
[
  {
    "app" = { "id" = "relaxed-griffon", ... }
    "audit" = { "id" = "enough-boa", ... }
  },
]
```

The whole map becomes the single element of a list. As a result, `[*].id` looks
for an `id` attribute on that array and returns an **empty list**, without a word
of warning. That is more dangerous than a clean error: the plan passes, and your
output is wrong.

The right form is a `for` expression:

```hcl
output "noms" {
  value = { for cle, r in random_pet.bucket : cle => r.id }
}
```

```text
{
  "app" = "relaxed-griffon"
  "audit" = "enough-boa"
}
```

If you insist on a list rather than a map, `values(random_pet.bucket)[*].id`
works, because `values()` first turns the map into a list.

## Over to you

You can now migrate from `count` to `for_each` without breaking what exists, and
read the proof in the plan. The challenge awaits on another setting: the
configuration shipped is **correct and already applied**, nothing is holed. It is
its architecture that has to change, without destroying.

```bash
dsoxlab run write-code-for-each
dsoxlab check write-code-for-each
dsoxlab hint write-code-for-each
```

Exam objective targeted: **2d** (Terraform Authoring and Operations
Professional), meta-arguments.

Reference: [for_each in Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/for-each-terraform/)
