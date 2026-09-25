# When exactly does Terraform read a data source?

Writing a `data` block is trivial. Knowing **when** Terraform reads it is much
less so, and yet that is what explains two frustrating situations: a plan showing
`(known after apply)` where you expected a value, and a plan announcing changes
although not a line of HCL moved.

This tutorial teaches the mechanism on a **throwaway** example: a weather station
reading thresholds and producing readings. Nothing to do with the challenge,
which will ask you to apply those same ideas to another case. Everything runs on
`local` and `random`, with no cloud and no VM.

## Setting up the example

Create a separate directory, outside the challenge, with a `seuils.txt` file and
a `main.tf`:

```text
seuil_alerte=38
station=eu-nord
```

```hcl
variable "cycle" {
  type    = number
  default = 1
}

resource "random_pet" "station" {
  length  = 2
  keepers = { cycle = var.cycle }
}

resource "local_file" "releve" {
  filename = "${path.module}/out/releve-${random_pet.station.id}.txt"
  content  = "cycle=${var.cycle}\n"
}
```

You will add the data sources as the sections go. First run `terraform init`
then `terraform apply` to start from a stable state.

## A read that stays known at plan time

Add a data source whose argument depends on no resource, only on a path:

```hcl
data "local_file" "seuils" {
  filename = "${path.module}/seuils.txt"
}
```

After an `apply`, ask the plan which data sources it intends to read:

```bash
terraform plan -out=tf.plan
terraform show -json tf.plan | jq '.resource_changes[] | select(.mode == "data")'
```

The output is empty. That is the sign the read **already happened during the
plan**: there is nothing to plan. You find it again, with its real values, in the
prior state:

```bash
terraform show -json tf.plan | jq '.prior_state.values.root_module.resources[].address'
```

```text
"data.local_file.seuils"
"local_file.releve"
"random_pet.station"
```

Everything that follows rests on that opposition: read at plan time, a data
source sits in `prior_state` and is absent from `resource_changes`.

## A read that shifts to apply time

Now add a data source reading back the file **produced** by `local_file.releve`,
by referencing its attribute. It is the reference that creates the dependency, do
not copy the path by hand:

```hcl
data "local_file" "releve_relue" {
  filename = local_file.releve.filename
}
```

Make the managed resource move by changing `cycle`, and look at the plan's data
sources:

```bash
terraform apply -auto-approve
terraform plan -var 'cycle=2' -out=tf.plan
terraform show -json tf.plan | jq -c '.resource_changes[] | select(.mode == "data") | {address, actions: .change.actions}'
```

```text
{"address":"data.local_file.releve_relue","actions":["read"]}
```

The read is deferred to apply time: it appears this time in `resource_changes`,
with `mode: data` and `actions: ["read"]`. Terraform cannot read it at plan time,
since the target file does not have its final name yet. Re-run the same command
without `-var 'cycle=2'` and the output goes back to empty: the same block swings
from one case to the other depending on the state of its dependency, without a
line changing.

## depends_on shifts nothing

This is the belief that has to be broken, and the heart of the coming challenge.
Add a third data source reading the same `seuils.txt`, with an explicit
dependency on top:

```hcl
data "local_file" "seuils_ordonnes" {
  filename   = "${path.module}/seuils.txt"
  depends_on = [random_pet.station]
}
```

With everything stable, count the deferred data sources:

```bash
terraform apply -auto-approve
terraform plan -out=tf.plan
terraform show -json tf.plan | jq '[.resource_changes[] | select(.mode == "data")] | length'
```

```text
0
```

Despite its `depends_on`, that data source is read at plan time, exactly like the
first. Many tutorials claim the opposite. Make the targeted resource move, and it
joins the deferred ones:

```bash
terraform plan -var 'cycle=2' -out=tf.plan
terraform show -json tf.plan | jq '.resource_changes[] | select(.mode == "data") | .address'
```

```text
"data.local_file.releve_relue"
"data.local_file.seuils_ordonnes"
```

So it is not `depends_on` that decides the deferral, but the fact that the
targeted resource is **configured to change in the current plan**.

## Where (known after apply) comes from

Expose both reads in outputs:

```hcl
output "seuils" {
  value = data.local_file.seuils.content
}

output "releve" {
  value = data.local_file.releve_relue.content
}
```

An output deriving from a deferred read cannot be known at plan time. The
`after_unknown` field confirms it:

```bash
terraform apply -auto-approve
terraform plan -var 'cycle=2' -out=tf.plan
terraform show -json tf.plan | jq -c '.output_changes | map_values(.after_unknown)'
```

```text
{"releve":true,"seuils":false}
```

`releve` carries `after_unknown: true`: that is the exact origin of the
`(known after apply)` you read in the plain plan. `seuils`, whose source is read
at plan time, stays known.

## The drift that does not come from your code

That consequence always surprises. Without touching a single `.tf`, change the
file being read:

```bash
terraform apply -auto-approve
terraform plan -detailed-exitcode ; echo "code = $?"
```

```text
code = 0
```

```bash
echo "seuil_max=45" >> seuils.txt
terraform plan -detailed-exitcode ; echo "code = $?"
```

```text
code = 2
```

Code `2` signals planned changes. A data source is re-read on every plan, and it
is that fresh read, not a value kept in state, that feeds the diff.

## What becomes of a data source at destroy time

Terraform does not destroy what it never created. The destruction plan ignores
data sources:

```bash
terraform plan -destroy -out=tf.plan
terraform show -json tf.plan | jq '[.resource_changes[] | select(.mode == "data")] | length'
```

```text
0
```

Go all the way, the nuance matters. Apply that plan, then list state:

```bash
terraform apply -auto-approve tf.plan
terraform state list
```

The output is empty. The data resources vanished from state along with the rest:
they are not destroyed, they simply stop existing. Saying a data source
"survives" a destroy would therefore be wrong.

## Over to you

You now know how to read a data source's timing in the JSON plan. The challenge
applies all of it to another setting, and checks every case:

```bash
dsoxlab run write-code-data-sources
dsoxlab check write-code-data-sources
dsoxlab hint write-code-data-sources
```

Keep in mind the only question that matters: the deferral criterion is never
"this data source has a dependency", but "does the resource it depends on change
in this plan?".

Exam objective targeted: **2b** (Terraform Authoring and Operations
Professional).

Reference: [Terraform data sources](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/data-sources/)
