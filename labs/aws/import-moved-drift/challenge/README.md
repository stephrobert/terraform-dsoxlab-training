# 🎯 Challenge: import, moved and drift

## Starting point

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

## ✅ Objective

1. **Import** the instance under the address `aws_instance.legacy`.
2. **Rename it** to `aws_instance.billing_api` with a `moved` block, and
   **apply it**. The `moved` block stays in place at the end.
3. **Cause a drift**: change the `Owner` tag by hand, outside Terraform.

   ```bash
   aws --endpoint-url http://localhost:14566 ec2 create-tags \
       --resources <id> --tags 'Key=Owner,Value=plateforme'
   ```

4. **Accept it**: align the code on reality, not the other way round.

## 🧭 The three traps, and why they are silent

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

## 🔍 Validation

```bash
dsoxlab check aws-import-moved-drift
```

Six tests. The `moved` is proven **without opening a `.tf`**: the test copies
your directory, puts the old address back into the copied state, and requires
the plan to carry a `previous_address` with `no-op`. Two exit codes must fall
together, the ordinary plan **and** `-refresh-only`: the first says reality
matches the code, the second that the state matches reality.
