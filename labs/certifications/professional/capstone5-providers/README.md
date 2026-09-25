# Two configurations of one provider, and an error to diagnose

The Professional's fifth objective is about providers: their architecture, their
configuration, their authentication, and diagnosing their errors. This capstone
holds them together.

The lab runs on **Floci**, a local AWS emulator: no account, no bill.

## One provider, several configurations

A provider is a **plugin**. Terraform downloads its binary, then hands it a
configuration. Nothing stops you handing it **several**:

```hcl
provider "aws" {
  region = "eu-west-3"
}

provider "aws" {
  alias  = "archives"
  region = "us-east-1"
}
```

`alias` is the only argument distinguishing the second from the first, and
without it Terraform refuses the duplicate. It is also what lets you **name** it:

```hcl
resource "aws_instance" "archives" {
  provider = aws.archives
}
```

A surprising point: **nothing is inherited** from one configuration to another.
Each carries its own options, credentials and endpoint. That is what allows two
regions, two accounts or two credential sets in a single configuration.

## The omission that does not show

Without the `provider` argument, a resource uses the **default** configuration.
It is therefore created in the wrong place, and **nothing flags it**: two EC2
instances look alike, and state does not say which configuration produced them.

The only place that says so is the JSON plan's `configuration` section:

```console
$ terraform show -json plan.tfplan | jq '.configuration.root_module.resources[]
    | {address, provider_config_key}'
{"address":"aws_instance.principal","provider_config_key":"aws"}
{"address":"aws_instance.archives","provider_config_key":"aws.archives"}
```

## The authentication error, and what it really says

The starting configuration fails, and the message names what it did not find:

```text
Error: No valid credential sources found
failed to refresh cached credentials, no EC2 IMDS role found
```

The provider looks for credentials **in order**: the environment, then `~/.aws`,
then the EC2 instance metadata. That last one does not exist outside an instance,
hence the final message.

Three options spare it those searches, and they do not do the same thing:

| Option | What it avoids |
| --- | --- |
| `skip_credentials_validation` | validating the identity with STS |
| `skip_requesting_account_id` | asking which account you belong to |
| `skip_metadata_api_check` | querying instance metadata |

Plus **non-empty** fake credentials, which the emulator accepts without checking.

## A proof that leaves Terraform

Measured while writing this lab: **Floci isolates by region**. An instance
created in `us-east-1` is invisible from a `eu-west-3` request.

The lab uses that: each instance must be seen in **its** region and **absent from
the other**. That proves, outside anything Terraform says, that two different
configurations produced them. A resource that had taken the default
configuration would show up on both sides in the same place.

## An environment without credentials

The tests run Terraform with no `AWS_*` variable and a `HOME` holding no `.aws`.
Without that precaution the lab would pass for whoever has credentials configured
and fail for everybody else: it would measure the machine, not the work.

## Over to you

```bash
dsoxlab run certifications-professional-capstone5-providers
dsoxlab check certifications-professional-capstone5-providers
dsoxlab hint certifications-professional-capstone5-providers
```

Six tests. The last one destroys both instances whatever happens: each is a real
container on Floci, holding a port.

Exam objective targeted: **5**, across its four sub-objectives.

Reference: [the Terraform Authoring and Operations Professional syllabus](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review)
