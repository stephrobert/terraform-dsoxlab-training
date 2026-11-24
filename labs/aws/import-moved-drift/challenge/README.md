# Take over an existing EC2, rename it, accept its drift

## The situation

**Exam objective targeted: 1e (manage state, import resources, reconcile drift).**

This lab covers the three traps reading a tutorial never reveals: a `moved` you
believe went through although it was never applied, a `moved` whose `from`
address is wrong and which Terraform ignores **in silence**, and drift you
overwrite by reflex instead of deciding what to do with it.

## Capability targeted

Bring under Terraform's control an EC2 instance created outside it, change its
logical address without the real object being recreated, then reconcile drift by
**accepting** reality, that is, by aligning the code with it rather than the
opposite.

## Where the learner starts

Floci runs locally on `localhost:14566` (Docker socket mounted, `-u root`). The
setup step created, **through the AWS CLI and not through Terraform**, an EC2
instance tagged `Name = legacy-billing-api` and `Owner = finops`. Its id is
dropped in `challenge/work/existing-instance.txt`.

Inside `challenge/work`: a **complete** `providers.tf` (an `aws` provider aiming
at Floci through an `endpoints` block, fake credentials,
`skip_credentials_validation`, `skip_requesting_account_id`,
`skip_metadata_api_check`), an `imports.tf` whose `import` block is holed
(`to = ???`, `id = ???`), **no `resource` block** (it is to be produced, not
copied), and no state.

## The state to reach

1. The instance appears in state with **the id already present in
   `existing-instance.txt`**: it was imported, not recreated.
2. Right after the import, the configuration is **faithful**: an ordinary plan
   proposes nothing. That is the real success criterion for an import, and the
   trap of automatic configuration generation, which produces extra arguments
   that must be removed.
3. The address in state is `aws_instance.billing_api`, although the import was
   done under another name, and the object's id **has not moved**: the rename
   went through a `moved` that was actually **applied**, a `plan` alone writing
   nothing to state.
4. The `moved` block is **still present** at the end of the lab. Removing it is a
   breaking change for anyone still starting from the old address.
5. The `Owner` tag was changed outside Terraform and the learner **accepts** that
   drift: on the Floci side the tag keeps its manual value, state reflects it,
   and so does the code. Both stopping criteria fall together: no drift left to
   reconcile, no change left to apply.
6. No extra instance exists on the Floci side: no destroy, no create.

## How it is proven

The tests query structured state, never the learner's `.tf` file:

- `terraform show -json`: one resource in `mode: managed` at address
  `aws_instance.billing_api`, whose `values.id` **equals** the id read from
  `existing-instance.txt`. Proof of the import and of the absence of recreation.
- `terraform plan -detailed-exitcode` exits **0**, and
  `terraform plan -refresh-only -detailed-exitcode` exits **0** as well. The
  first proves reality matches the code, the second that state matches reality.
- The AWS CLI pointed at Floci shows the `Owner` tag at its **manual** value, and
  returns a single non-terminated instance: drift was accepted and the code
  aligned, without recreation.
- Proof of the `moved`: the test copies the working directory aside, rewrites the
  address in the copied state back to its old name, runs `terraform plan -out`
  and reads the plan as JSON. It requires an entry carrying `previous_address`
  with `actions: ["no-op"]`. A deleted `moved`, or one whose `from` is wrong,
  would produce a `create`, without the slightest error.

## 🎯 Challenge: import, moved and drift

### Starting point

An EC2 instance **already exists**. It was created by hand, outside Terraform,
and carries the tags `Name = legacy-billing-api` and `Owner = finops`.

`challenge/work` holds `providers.tf` (**complete**) and `imports.tf` (**full of
holes**). There is **no `resource` block**: it is to be produced, not copied. No
state.

Nobody hands you the instance identifier: finding it is the first step of an
import.

```bash
aws --endpoint-url http://localhost:14566 ec2 describe-instances \
    --filters 'Name=tag:Name,Values=legacy-billing-api' \
              'Name=instance-state-name,Values=running' \
    --query 'Reservations[].Instances[].InstanceId' --output text
```

### ✅ Objective

1. **Import** the instance under the address `aws_instance.legacy`.
2. **Rename it** to `aws_instance.billing_api` with a `moved` block, and
   **apply it**. The `moved` block stays in place at the end.
3. **Cause a drift**: change the `Owner` tag by hand, outside Terraform.

   ```bash
   aws --endpoint-url http://localhost:14566 ec2 create-tags \
       --resources <id> --tags 'Key=Owner,Value=plateforme'
   ```

4. **Accept it**: align the code on reality, not the other way round.

### 🧭 The three traps, and why they are silent

- **A `plan` alone writes nothing into the state.** You believe the `moved`
  went through; it did not.
- **A `moved` with a wrong `from` is ignored without any warning.** Terraform
  finds nothing at that address, says nothing, and creates the new resource. The
  real object ends up **duplicated**.
- **Overwriting a drift is a reflex.** An `apply` "puts things back in order"
  and erases a change that may have been deliberate. The colleague who made it
  will never know why their tag vanished.

And a fourth one, about the import itself: **the resource being in the state is
not enough**. As long as an ordinary plan proposes something, the import is not
finished. `-generate-config-out` produces arguments the API returns and the
configuration has no business carrying.

### 🔍 Validation

```bash
dsoxlab check aws-import-moved-drift
```

Six tests. The `moved` is proven **without opening a `.tf`**: the test copies
your directory, puts the old address back into the copied state, and requires
the plan to carry a `previous_address` with `no-op`. Two exit codes must fall
together, the ordinary plan **and** `-refresh-only`: the first says reality
matches the code, the second that the state matches reality.
