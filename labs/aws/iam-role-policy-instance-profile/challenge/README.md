# 🎯 Challenge: compose the IAM chain without mixing up the words

## Starting point

`challenge/work` holds four files. `versions.tf` and `variables.tf` are
**provided and complete**. `main.tf` and `outputs.tf` are **full of holes**.

Floci runs locally: no AWS account, no bill.

## ⚠️ Two wordings not to repeat

Many tutorials, some guides included, say both of these. Both are wrong.

- "the **resource policy** of the role" for its permissions. The only
  resource-based policy IAM knows for a role is its **trust policy**, the one
  saying *who* may assume it. Permissions live in a separate object.
- "an instance profile carries **one or more roles**". AWS allows **exactly
  one**. The Terraform argument is `role`, singular. The API's `Roles` field is
  an array because it always has been, not because you can put two in it.

## ✅ Objective

1. **The trust policy**: a `principals` block of type `Service` targeting
   `ec2.amazonaws.com`, for the `sts:AssumeRole` action.
2. **The permissions**: two statements, and **two different ARNs**.
   `s3:ListBucket` applies to the bucket, `s3:GetObject` to its objects.
3. **The role** carries the first document, and **nothing else**.
4. **The policy** carries the second, and becomes a real IAM object.
5. **The profile** receives the role, **the instance** receives the profile
   name.
6. **The five outputs**, the only way to show the tests the produced JSON
   without reading your `.tf`.

## 🧭 What the lab makes you observe

- **Both documents are in `mode: data`** although no network call happens.
  "data" does not mean "remote", it means **read**.
- **A policy carrying only the bucket ARN lets you list and refuses to read.**
  That is the most common IAM-on-S3 mistake, and the AWS message does not say
  why.
- **`get-instance-profile` returns a `Roles` array with a single element.**
- **Removing the attachment destroys only it**: the role and the policy survive.
  That is what tells an attachment from an ownership.

## 🔍 Validation

```bash
dsoxlab check aws-iam-role-policy-instance-profile
```

Seven tests. The produced JSON arrives through `terraform output -json` then is
deserialised; the inventory comes from `show -json`; and what the emulator
**actually received** is read back through the AWS API. The last test removes
the attachment on a **copy** of your work: a test does not break what it
measures. None reads your `.tf`.
