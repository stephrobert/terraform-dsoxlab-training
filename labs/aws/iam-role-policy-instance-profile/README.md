# IAM: the role, its two policies, and the profile that carries only one

IAM has a reputation for being confusing. It mostly is because of two words
people use interchangeably, and an array that suggests a freedom which does not
exist. This tutorial settles both.

## A data source that queries nothing

`aws_iam_policy_document` makes **no network call**. It is a JSON builder,
written in HCL, saving you from burying JSON inside a string.

```hcl
data "aws_iam_policy_document" "confiance" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ec2.amazonaws.com"]
    }
  }
}
```

It still shows up as `"mode": "data"` in the state, exactly like a data source
calling an API. A good occasion to remember what that mode really means:
**read**, not **remote**. Terraform neither creates nor destroys it, and
recomputes it on every plan.

## A role's two policies, and their real names

An IAM role carries **two** things, unrelated to each other.

| | What it says | Where it lives |
|---|---|---|
| **trust policy** | **who** may assume the role | in the role, `assume_role_policy` |
| **permissions policy** | **what** the role may do | in a separate, attached object |

The trust policy is the only **resource-based** policy IAM knows for a role. If
a text calls the permissions policy a "resource policy", it is wrong, and that
confusion is expensive when debugging a denial.

```hcl
resource "aws_iam_role" "application" {
  name               = "role-application"
  assume_role_policy = data.aws_iam_policy_document.confiance.json
}

resource "aws_iam_policy" "lecture_s3" {
  name   = "policy-lecture-s3"
  policy = data.aws_iam_policy_document.permissions.json
}

resource "aws_iam_role_policy_attachment" "lecture" {
  role       = aws_iam_role.application.name
  policy_arn = aws_iam_policy.lecture_s3.arn
}
```

Three objects, deliberately: an attached policy can serve several roles.
Removing the attachment destroys neither.

## S3's two ARNs, and the denial nobody understands

Here is the most common IAM-on-S3 mistake:

```hcl
# Incomplete: you will be able to list, never to read.
statement {
  actions   = ["s3:ListBucket", "s3:GetObject"]
  resources = ["arn:aws:s3:::mon-bucket"]
}
```

Listing applies to the **bucket**, reading applies to its **objects**. Two
different resources:

```hcl
statement {
  actions   = ["s3:ListBucket"]
  resources = ["arn:aws:s3:::mon-bucket"]
}

statement {
  actions   = ["s3:GetObject"]
  resources = ["arn:aws:s3:::mon-bucket/*"]
}
```

<Aside type="caution" title="AWS will not tell you why">
An `AccessDenied` on `GetObject` does not mention the missing ARN. You will see
a policy that does contain `s3:GetObject`, and a denial anyway. The `/*` suffix
is the first thing to check.
</Aside>

## One profile, one role, and a misleading array

```bash
aws iam get-instance-profile --instance-profile-name profil-application
```

```json
{ "InstanceProfile": { "Roles": [ { "RoleName": "role-application" } ] } }
```

`Roles` is an **array**, and many conclude you can put several in it. **You
cannot.** AWS allows exactly one, and the Terraform argument says so plainly:
`role`, singular. The array is an API legacy, not a possibility.

The instance receives the profile **name**:

```hcl
resource "aws_instance" "application" {
  iam_instance_profile = aws_iam_instance_profile.application.name
}
```

## Over to you

You now know that a data source can be purely local, that the trust policy and
the permissions are two distinct objects, that S3 requires two ARNs, and that a
profile carries only one role despite what its API suggests.

```bash
dsoxlab run aws-iam-role-policy-instance-profile
dsoxlab check aws-iam-role-policy-instance-profile
dsoxlab hint aws-iam-role-policy-instance-profile
```

Exam sub-objective covered: **2b** (use data sources).

Reference: [IAM role, policy and instance profile](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/iam-role-policy-instance-profile/)
