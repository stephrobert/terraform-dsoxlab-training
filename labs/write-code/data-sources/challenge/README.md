# Mastering when a data source is read

## The situation

**Exam objective targeted: 2b, use data sources.**

Writing a `data` block is trivial. Knowing **when** Terraform reads it is much
less so, and that is what explains a plan moving without any code change.

## Capability targeted

Build a configuration where each data source's read timing is deliberate: one
read at plan time, the other deferred to apply time because it depends on a
resource being changed. Prove the difference in the JSON.

## Where the learner starts

`challenge/work` rests solely on the `local`, `null` and `random` providers: no
cloud, no VM, no cost. The directory is bare, with no `.terraform/`, no lock file
and no state. It holds an already filled `catalogue.txt`, a complete
`versions.tf`, and a `main.tf` holed with `???`: the argument of a data source
that must stay known at plan time, that of a second one that must on the contrary
depend on a resource the configuration produces, and the outputs exposing both
reads. A callout in the guide claims `depends_on` is enough to force the read to
apply time: that is false, and the lab is built to observe it.

## The state to reach

1. The directory is initialised and the lock file exists.
2. One data source reads the supplied file with an argument known at plan time.
   It appears in `prior_state` with its real values, in no `resource_changes`
   entry, and the output deriving from it is known from the plan onwards.
3. A second data source reads a file produced by a managed resource of the
   configuration. On the initial plan it appears in `planned_values` and in
   `resource_changes` with `"mode": "data"` and `"actions": ["read"]`, and the
   output deriving from it is unknown.
4. A third data source carries an explicit `depends_on` towards a managed
   resource. Once that resource is created and stable, a new plan reads it at
   plan time: the deferral is due to the pending change, not to the `depends_on`
   alone.
5. After the apply, state carries the data sources as `mode: data` and the
   managed resources as `mode: managed`, and replaying a plan announces nothing.
6. Changing `catalogue.txt` without touching a `.tf` file makes a pending change
   appear: the drift comes from the external data.
7. The destruction plan holds no action bearing on a data source: Terraform does
   not destroy what it never created.

## How it is proven

No test reads back the learner's `.tf`, and none parses human output.

- The plan is saved then converted by `terraform show -json`: the tests walk
  `prior_state`, `planned_values`, `resource_changes` and `output_changes` and
  locate each data source through `mode`, `actions` and `after_unknown`.
- `terraform show -json` on the final state sorts each address by `mode`, which
  rules out passing a managed resource off as a data source, and
  `terraform output -json` confirms the values read.
- `terraform plan -detailed-exitcode` exits 0 after the apply, then 2 once the
  input file has been changed: the drift is proven by an exit code.
- The destruction plan is converted to JSON: no `mode: data` entry in
  `resource_changes`.

## 🎯 Challenge: when does Terraform read a data source?

### Starting point

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

### ✅ Objective

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

### 🧭 How to observe it for yourself

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

### 🔍 Validation

```bash
dsoxlab check write-code-data-sources
```

Twelve tests. They walk `prior_state`, `resource_changes`, `output_changes` and
each state address's `mode`. Copying the catalogue's content into a `local_file`
instead of reading it would produce `mode: managed` and be detected.
