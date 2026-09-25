# `sensitive` protects the screen, not the state

The Professional's objective 6 is assessed **by multiple choice**, and needs no
account. But what it teaches is measurable, and this lab measures it on a real
provider against a local emulator.

It closes on an assumption almost everyone makes once.

## The measurement

A variable marked `sensitive`, written into a resource tag. On 2026-09-25, with
Terraform 1.16.1:

```console
$ terraform show | grep Jeton
    "Jeton" = (sensitive value)

$ grep -c 'svc-7f3a91c4e2b8-prod' terraform.tfstate
2
```

The annotation did its job: Terraform never printed the value. And the state
holds it in clear text, twice, in `tags` and in `tags_all`. A saved plan holds it
too.

`sensitive` acts on **output**, not on storage. A state is read, backed up,
shared and sometimes committed by mistake: anything that lands in it is
disclosed.

## What to store instead of a secret

A **fingerprint**, whenever the point is to *check* rather than to *replay*:

```hcl
tags = {
  Empreinte = sha256(var.jeton_de_service)
}
```

It proves a presented token is the expected one, and it cannot give the token
back. Exactly the reasoning behind never storing a password.

## Where credentials do live

Not in the configuration. HCP Terraform puts them in the **run environment**,
just before the plan or the apply, and the AWS provider picks up
`AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY` from there when the configuration
gives it nothing.

That is what makes one configuration work everywhere: with a workspace's static
keys, with dynamic credentials, or with a role assumed on a workstation. The file
is written to **receive** credentials, not to contain them.

Careful though, and it is measurable: with no credentials **anywhere**, the AWS
provider answers `No valid credential sources found` and will not even plan.
Removing the keys is half the work; the environment has to supply them.

## Dynamic credentials, in seven steps

Static credentials are a risk "even if you rotate them regularly". Dynamic
provider credentials replace them with credentials minted per run:

1. HCP Terraform generates a **workload identity token**, OIDC-compliant,
   carrying the organization, the workspace and the **run stage**;
2. when a plan or apply starts, it sends that token to the cloud platform;
3. the platform verifies it with **HCP Terraform's public signing key**;
4. if that succeeds, it returns a set of **fresh temporary credentials**;
5. HCP Terraform places them in the run environment for the provider;
6. the plan or apply proceeds;
7. when it completes, **the environment is torn down and the credentials are
   discarded**.

Hence the property worth remembering: a credential that does not outlive its run
does not need rotating. Setting it up takes three steps — a trust relationship,
roles and policies on the platform, and environment variables on the workspace —
and self-hosted agents must be on **v1.7.0** or newer.

## The token, and why you do not need one

This lab needs **no HCP Terraform account**, and nothing runs remotely. If you
come across

```
Error: Required token could not be found
```

your configuration was accepted: Terraform has reached the authentication step,
and the lab deliberately stops there.

To go beyond it, a token takes three minutes to create and place, and
[`docs/hcp-token.md`](../../../docs/hcp-token.md) says where to put it and which
location wins when several are filled:

```bash
python3 scripts/diagnostic-jeton-hcp.py --verifier
```

## Over to you

```bash
dsoxlab run hcp-terraform-shared-credentials
dsoxlab check hcp-terraform-shared-credentials
dsoxlab hint hcp-terraform-shared-credentials
```

Eight tests. They apply your configuration in a run environment they build
themselves, stripped of every `AWS_*` on the machine and with no `~/.aws`, then
read the state and sweep the whole file for the token.

Exam objective targeted: **6c**.

Reference: [dynamic provider credentials](https://developer.hashicorp.com/terraform/cloud-docs/workspaces/dynamic-provider-credentials)
