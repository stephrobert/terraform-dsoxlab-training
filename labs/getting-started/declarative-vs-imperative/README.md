# Declarative against imperative: convergence is proven

"Terraform is declarative" is a sentence people repeat without checking it. It
does not mean the code is prettier, nor that there are fewer lines. It describes
a **measurable property**: applying twice gives the same result as applying
once. This tutorial shows where a script loses that property, and how to prove
it rather than take it on trust.

## The script is not at fault step by step

Take this script, which builds a report with an identifier:

```bash
mkdir -p "$SORTIE"
IDENTIFIANT="$(tr -dc 'a-z0-9' < /dev/urandom | head -c 8)"
printf 'rapport genere, identifiant : %s\n' "$IDENTIFIANT" >> "$SORTIE/rapport.txt"
```

Every line is reasonable. `mkdir -p` is even explicitly idempotent. The fault is
in none of them: it is that **the result depends on the number of runs**. Two
calls give two identifiers, and a two-line report. Ten calls give ten.

That is the common trait of the imperative: you describe *how to do it*, and
doing it twice is not doing it once.

## Describing a state means giving up describing the steps

The same intent, expressed in Terraform:

```hcl
resource "random_string" "identifiant" {
  length  = 8
  special = false
  upper   = false

  keepers = {
    projet = "declaratif"
  }
}

resource "local_file" "rapport" {
  content  = "rapport genere, identifiant : ${random_string.identifiant.result}\n"
  filename = "${path.module}/sortie-declarative/rapport.txt"
}
```

Nothing here says "draw an identifier". The text says: *there is an eight
character identifier, and a file whose content carries it*. Terraform compares
that description to the state, and acts only on the gap.

## keepers: what allows a new draw

A random value raises an obvious question: why does it not change on every
`apply`? Because it is **remembered in the state**, and the provider only drops
it if **`keepers`** changes.

```hcl
keepers = {
  projet = "declaratif"   # fixed: the identifier will never be dropped
}
```

```hcl
keepers = {
  version = var.version_du_rapport   # moves with the variable: new draw
}
```

That is the handle you keep on randomness. The script has none: `/dev/urandom`
remembers nothing.

## triggers: depending on the right thing

`null_resource` accepts a **`triggers`** block, a map of values whose change
forces its **replacement**:

```hcl
resource "null_resource" "empreinte" {
  triggers = {
    identifiant = random_string.identifiant.result
  }
}
```

It will be replaced if the identifier changes, and **only** then. Same logic as
`keepers`, applied to an action rather than to a value.

## Idempotence is read from an exit code

Never judge a plan by eye. The command answers with a code:

```bash
terraform plan -detailed-exitcode ; echo $?
```

| Code | Meaning |
|---|---|
| `0` | no change |
| `1` | error |
| `2` | changes are planned |

Right after an `apply`, that code must be `0`. It is the machine proof of
convergence, and it depends on no wording.

## Drift, and what it does not take with it

Delete the report outside Terraform:

```bash
rm sortie-declarative/rapport.txt
terraform plan -detailed-exitcode ; echo $?   # 2
```

Save the plan and read it as JSON:

```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan | jq '.resource_changes[] | select(.change.actions != ["no-op"]) | {address, actions: .change.actions}'
```

```text
{"address": "local_file.rapport", "actions": ["create"]}
```

**A single create.** The identifier is not dropped, the `null_resource` is not
replaced. Repair happens with an `apply`, **without touching the code**, and the
identifier from before the drift is still there.

<Aside type="caution" title="A manual fix is not a convergence">
Recreating the file by hand would put a report in the right place, and leave the
state disagreeing with reality down to the first detail. The tool repairs, not
you: that is the whole point of having described a state.
</Aside>

## Over to you

You now know that an imperative script diverges because its result depends on
the number of runs, that a configuration describes a state Terraform compares to
the state file, that `keepers` and `triggers` are your handles on randomness and
on replacements, that idempotence is read from an exit code, and that drift is
repaired where it happened.

The challenge has you translate the provided script, then produce those proofs.

```bash
dsoxlab run getting-started-declarative-vs-imperative
dsoxlab check getting-started-declarative-vs-imperative
dsoxlab hint getting-started-declarative-vs-imperative
```

Exam sub-objective covered: **1b** (`plan`: prove idempotence, detect drift and
fix it).

Reference: [Declarative vs imperative](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/declaratif-vs-imperatif/)
