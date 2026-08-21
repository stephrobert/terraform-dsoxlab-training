# The S3 lock does not turn itself on

Two beliefs trip candidates up on this objective. That declaring a
`backend "s3"` is enough to **lock** the state. And that a `backend` block takes
variables, like the rest of HCL. Both are wrong, and both can be measured.

## A `backend` block refuses any named value

```hcl
terraform {
  backend "s3" {
    bucket = var.backend_bucket
  }
}
```

```text
Error: Variables not allowed

  on main.tf line 8, in terraform:
   8:     bucket = var.backend_bucket

Variables may not be used here.
```

`init` exits with **1**. The backend is read **before** variables are evaluated:
it cannot know anything about them. That is the reason **partial configuration**
exists, not a mere convenience.

## Partial configuration, in a file

The block stays **empty**, and the arguments arrive at init time:

```bash
terraform init -backend-config=floci.s3.tfbackend
```

The **file** form beats `-backend-config="key=value"`, which the documentation
discourages for secrets since the shell history keeps them. The recommended
naming is `*.<backend>.tfbackend`.

## Check what Terraform actually retained

Those values then appear in **no** `.tf` file. Terraform writes them down anyway,
and that is the only reliable proof:

```bash
jq '{type: .backend.type, config: .backend.config}' .terraform/terraform.tfstate
```

```text
{
  "type": "s3",
  "config": {
    "bucket": "tf-state-lab",
    "key": "producer/terraform.tfstate",
    "use_path_style": true,
    "use_lockfile": true,
    "endpoints": { "s3": "http://localhost:14566" }
  }
}
```

Careful, that file is **not a vault**: the configuration sits there fully
**resolved**, credentials included. Partial configuration protects the
**repository**, not the **disk**.

## Locking is a strict opt-in

This is the heart of the lab. `use_lockfile` defaults to **`false`**. Drop a
`.tflock` next to the state, then plan.

With `use_lockfile = true`:

```text
Error: Error acquiring the state lock

Error message: operation error S3: PutObject, https response error
```

Exit **1**. Without the argument, and with the **same** object still in place,
the plan succeeds with exit **0**: the lock is simply **ignored**, and two
concurrent applies overwrite each other silently.

Native S3 locking landed in Terraform **1.10**. The **DynamoDB** table lock is
deprecated.

## After migration, nothing is left locally

Many tutorials follow the migration with `rm -rf terraform.tfstate`. Measured,
there is **nothing** to delete:

```text
producer local state: NONE
objects in the bucket: ['producer/terraform.tfstate']
```

## `defaults` fills a gap, not an absence

The argument provides a fallback "in case the state file is empty or lacks a
required output". The nuance matters:

- the state **exists** but the output is **missing**: the fallback **applies**;
- the state key does **not exist**: Terraform returns
  `Error: Unable to find remote state`, exit **1**.

So `defaults` does not replace an `apply` of the upstream stack.

## Your turn

```bash
dsoxlab run aws-backend-s3-remote-state
dsoxlab check aws-backend-s3-remote-state
dsoxlab hint aws-backend-s3-remote-state
```

The S3 emulator is declared under `runtime.services`: **dsoxlab starts it for
you**, on `http://localhost:14566`. No AWS account is needed.

Exam sub-objective covered: **3b**, with **3d** in support.

Reference: [S3 backend and terraform_remote_state](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/backend-s3-remote-state/)
