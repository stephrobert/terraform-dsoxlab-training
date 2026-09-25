# Two configurations, one shared state, no interaction

The Professional's third objective is the team one: pin versions, share state,
run without a human confirming anything. This capstone has **two separate
configurations** collaborate.

`reseau/` publishes, `application/` consumes. The lab runs on **Floci**, which
provides the S3 backend: no AWS account, no bill.

## No expression crosses the boundary

That is the rule governing everything else. Two configurations share neither
variables, nor locals, nor resources. The **only** bridge is reading remote
state, through its **declared outputs**:

```hcl
data "terraform_remote_state" "reseau" {
  backend = "s3"
  config  = { bucket = "capstone3-etats", key = "reseau/terraform.tfstate", ... }
}
```

Direct consequence: what the upstream does not expose as an `output` is
**invisible** from the other side, even if the value sits in its state. A shared
stack's outputs are not decoration, they are its **contract**.

## A `backend` block accepts no named value

```hcl
backend "s3" {
  bucket = var.backend_bucket   # Error: Variables not allowed
}
```

The backend is resolved **before** any expression is evaluated: you must know
where to read state before you can read anything. That is why **partial**
configuration exists:

```hcl
backend "s3" {}
```

```bash
terraform init -backend-config=backend.tfbackend
```

The file form is preferable to `-backend-config="key=value"`, which the
documentation advises against for a secret: the shell history keeps it.

## The two-step cycle, and what it closes

```bash
terraform plan -out=tf.plan -input=false
terraform apply -input=false tf.plan
```

A direct `apply` **re-reads the configuration** when applying. Between review and
application somebody may have pushed a commit: what was reviewed is therefore not
necessarily what goes out.

Applying a **saved** plan closes that gap. And `-input=false` guarantees no
question waits for an answer nobody will give: a CI that asks a question is a CI
that times out.

## The only proof worth having: change the upstream

Everything else could be obtained by copying three values by hand. The decisive
test replays `reseau/` with a different range, then requires the downstream to
**follow**:

```console
$ cd reseau && terraform apply -var 'plage_reseau=10.77.0.0/16'
$ cd ../application && terraform plan -detailed-exitcode ; echo $?
2
```

A `0` there would mean the downstream reads nothing: its values are frozen. That
is exactly what this test exists to catch.

## Over to you

```bash
dsoxlab run certifications-professional-capstone3-collaborative-workflows
dsoxlab check certifications-professional-capstone3-collaborative-workflows
dsoxlab hint certifications-professional-capstone3-collaborative-workflows
```

Seven tests. None reads your `.tf`: the backend is proven by the absence of local
state and the presence of both keys in the bucket, remote reading by a
`mode: data` entry of type `terraform_remote_state`, and the constraints by the
lock file.

Exam objective targeted: **3**, across its four sub-objectives.

Reference: [Professional exercises](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/certifications/professional/exercices/)
