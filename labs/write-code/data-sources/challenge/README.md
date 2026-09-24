# 🎯 Challenge: when does Terraform read a data source?

## Starting point

`challenge/work` holds two managed resources already written, and **three `data`
blocks plus two `output` blocks left commented out**, each holed with a `???`.
Every hole carries above it a comment stating what is expected.

The configuration therefore applies **as it stands**. Start there, and you will
have a stable starting point:

```bash
terraform init
terraform apply
```

Then uncomment one block at a time and complete it. It is the comparison between
two steps that makes the subject click, not the final result: the tutorial
(`README.md`) gives, for each one, the observation command and the expected
output.

Do not touch `versions.tf`, `variables.tf` or `catalogue.txt`.

## ✅ Objective

1. **A read known at plan time.** `data.local_file.catalogue` reads
   `catalogue.txt`. Its argument must reference no managed resource: only
   `path.module`.

2. **A deferred read.** `data.local_file.rapport_relu` reads back the file
   **produced** by `local_file.rapport`, by referencing its `filename`
   attribute. Do not rebuild the path by hand: it is the reference that creates
   the dependency, hence the deferral.

3. **A `depends_on` that defers nothing.** `data.local_file.catalogue_ordonne`
   reads the same `catalogue.txt` as the first one, with an explicit
   `depends_on` towards `random_pet.empreinte` on top. Once that resource is
   stable, it is read **at plan time**, exactly like the first. That is the
   heart of the lab.

4. **Two outputs.** `catalogue` exposes the first read, known from the plan
   onwards. `rapport` exposes the second, unknown on the initial plan.

After your `apply`, `terraform plan` must propose nothing.

## 🧭 How to observe it for yourself

It is the hands-on part that makes the subject click:

```bash
terraform apply
terraform plan -out=tf.plan
terraform show -json tf.plan | jq '.resource_changes[] | {address, mode, actions: .change.actions}'
```

Nothing should appear. Then set the managed resource in motion:

```bash
terraform plan -var 'revision=2' -out=tf.plan
terraform show -json tf.plan | jq '.resource_changes[] | select(.mode == "data")'
```

This time `rapport_relu` shows up with `"actions": ["read"]`. Compare with
`catalogue_ordonne`, which carries a `depends_on` all the same.

## 🔍 Validation

```bash
dsoxlab check write-code-data-sources
```

Twelve tests. They walk `prior_state`, `resource_changes`, `output_changes` and
each state address's `mode`. Copying the catalogue's content into a `local_file`
instead of reading it would produce `mode: managed` and be detected.
