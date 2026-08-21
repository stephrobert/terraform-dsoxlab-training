# 🎯 Challenge: measure what the lock blocks, and what it lets through

## ✅ Objective

In `challenge/work`, two files carry `???` markers. To do:

1. **`main.tf`**: set the `path` of the `backend "local"` block to
   **`etat/projet.tfstate`** (the state must leave the root), and give the
   provisioner a command that holds the apply for **at least fifteen seconds**;
2. **`observations.tf`**: take the measurements, then fill the four outputs with
   what you actually **observed**.

Measurements are taken from a second terminal while a `terraform apply` runs in
the first one. Record **exit codes** (`echo $?`), not messages:

```bash
terraform plan -input=false > /dev/null 2>&1; echo $?
```

For `verrou_residuel`, kill the running apply (`kill -9`), check whether the lock
file is still there, run a `plan` again, note its exit code, then look for the
file once more.

For `backend_s3`, the answer is in the official S3 backend page: the name of the
locking argument, its default value, and the status of DynamoDB table based
locking.

## 🔍 Validation

`dsoxlab check state-state-locking` **redoes the experiment** and compares its
own measurements with yours:

- `.terraform/terraform.tfstate` carries `backend.type = local` and
  `backend.config.path = etat/projet.tfstate`;
- the replacement apply does last at least fifteen seconds, otherwise no lock is
  observable and nothing can be measured;
- the captured lock carries **seven** fields, a UUID `ID`, your CLI `Version`,
  and a `Path` that designates the state;
- your four outputs are checked against the test's own readings, action by
  action;
- no lock file remains at the end, and `plan -detailed-exitcode` returns 0.

Stuck? `dsoxlab hint state-state-locking`.
