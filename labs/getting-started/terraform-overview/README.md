# Terraform, and what it keeps in memory

Terraform is often introduced as "a tool that reads `.tf` files and calls APIs".
True, and not enough: that description does not explain why a second `apply`
recreates nothing, why deleting a file by hand produces a non-empty plan, or why
renaming a resource in the code can **destroy** it. All of this comes from a
single object, the **state**.

This tutorial shows it on a purely local configuration: three providers, no
cloud account, no cost. The challenge will then have you prove each of these
behaviours.

## The state is not a cache

A cache can be thrown away: the data is still at the source. The state cannot.
It holds the **mapping** between an address in your code, say
`local_file.rapport`, and a real object identified by its `id` at the provider.
Throw the state away and Terraform no longer knows that object is his: it will
offer to **create it again**.

```bash
terraform show -json | jq '.values.root_module.resources[] | {mode, type, address}'
```

```text
{"mode": "managed", "type": "random_pet",  "address": "random_pet.nom"}
{"mode": "managed", "type": "local_file",  "address": "local_file.rapport"}
{"mode": "data",    "type": "local_file",  "address": "data.local_file.inventaire"}
```

Two modes coexist, and the distinction is not decorative.

## managed against data: what Terraform will destroy

A resource in **`managed`** mode is Terraform's responsibility: it created it, it
will change it, it will **destroy** it on `destroy`. An entry in **`data`** mode
is only *read*: it is resolved on every plan, appears in no `destroy`, and
removing it from the code erases nothing on disk.

```hcl
# Terraform creates this file, and will delete it.
resource "local_file" "rapport" {
  content  = "..."
  filename = "${path.module}/rapport.txt"
}

# Terraform reads this file, and will never touch it.
data "local_file" "inventaire" {
  filename = "${path.module}/inventaire.txt"
}
```

The practical consequence is blunt: declaring as a `resource` a file somebody
wrote by hand is granting yourself the right to delete it. An object nobody
declared, on the other hand, stays perfectly invisible to Terraform. It does not
watch it, does not back it up, and will never complain about it.

## The reference is the dependency

There are two ways to write a file containing a generated name. They produce the
**same file on disk**, and they are not worth the same:

```hcl
# No: the value is pasted. No dependency, and if the name changes,
# the report lies.
content = "ressource generee : clever-mongrel\n"

# Yes: the value is BUILT. Terraform now knows the report depends on the
# name, and orders the operations accordingly.
content = "ressource generee : ${random_pet.nom.id}\n"
```

Terraform does not read your intent: it builds a graph from the **references**
it finds in expressions. No reference, no edge, no guaranteed order.

## Idempotence is proven by an exit code

"The plan is empty" is not something to check by eye. The command answers with a
code:

```bash
terraform plan -detailed-exitcode
echo $?
```

| Code | Meaning |
|---|---|
| `0` | no change: code, state and reality are aligned |
| `1` | error |
| `2` | changes are planned |

That is the form to use in a script or a test: it depends on no wording, and it
will not move at the next release.

## Drift, and what survives it

Delete the report outside Terraform, then ask for a plan. Terraform first
refreshes its state, sees the object is gone, and offers to recreate it. What
matters is **what it does not offer**:

```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan | jq '.resource_changes[] | {address, actions: .change.actions}'
```

```text
{"address": "local_file.rapport", "actions": ["create"]}
{"address": "random_pet.nom",     "actions": ["no-op"]}
```

The `random_pet` is **intact**. That is the whole point of the stored mapping:
without it Terraform would not know this name already exists, would regenerate
it, and the recreated report would carry a different name. Drift is repaired
where it happened, not everywhere.

## sensitive hides the display, and nothing else

Last point, and the most misunderstood one. Marking an output `sensitive` changes
**one thing only**: what Terraform prints on screen.

```hcl
output "nom_majuscule" {
  value     = upper(random_pet.nom.id)
  sensitive = true
}
```

```bash
terraform output
```

```text
nom_animal     = "clever-mongrel"
nom_majuscule  = <sensitive>
```

Now open `terraform.tfstate`:

```json
"nom_majuscule": {"value": "CLEVER-MONGREL", "type": "string", "sensitive": true}
```

The value is there **in the clear**. The flag was indeed recorded, but it
describes a display intent, not a protection.

<Aside type="caution" title="A state file is sensitive data">
Everything your resources handle ends up in the state, including generated
passwords and values marked `sensitive`. A state is stored like a secret:
restricted access, encryption at rest, never in a git repository. To keep a value
out of it entirely you need `ephemeral = true`, not `sensitive`.
</Aside>

## Over to you

You now know that the state carries the mapping between code and reality, that
`managed` and `data` do not commit to the same responsibility, that a reference
creates a dependency where a pasted value creates none, that idempotence is read
from an exit code, that drift spares what did not move, and that `sensitive`
encrypts nothing.

The challenge has you establish these six facts on a configuration full of
holes, and the tests prove them in the JSON.

```bash
dsoxlab run getting-started-terraform-overview
dsoxlab check getting-started-terraform-overview
dsoxlab hint getting-started-terraform-overview
```

Exam sub-objective covered: **1e** (state, import, drift).

Reference: [Terraform overview](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/presentation-terraform/)
