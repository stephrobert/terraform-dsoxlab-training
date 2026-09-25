# Scenario: credentials live neither in the code nor in the state

**Exam objective targeted: 6c, manage provider credentials in HCP Terraform.**

Objective 6 is assessed by multiple choice, but what it teaches can be measured, and this
lab measures it on a real provider against a local emulator. No account, no card.

A team ships a configuration that works. The provider carries its keys in the file, and a
service token is written into a tag; the variable is marked `sensitive`, so everyone
assumes it is protected. The state, which everyone reads, says otherwise.

## Capability targeted

Write a configuration that **receives** its credentials instead of containing them, as HCP
Terraform provides them in the run environment, and stop a secret from reaching the state,
which `sensitive` does not prevent.

## Where the learner starts

`challenge/work` holds two directories:

1. `configuration/`, an AWS configuration pointed at the emulator. Its provider carries
   `access_key` and `secret_key` in clear text, and its instance carries a `Jeton` tag
   holding the service token. `jeton.auto.tfvars` supplies the value.
2. `questionnaire/`, five answers to place in `reponses.auto.tfvars`, on dynamic
   credentials.

## The state to reach

1. The provider no longer declares any credentials. It finds them in its environment,
   `AWS_ACCESS_KEY_ID` and `AWS_SECRET_ACCESS_KEY`, which is where HCP Terraform puts them.
2. The instance no longer carries the token. An `Empreinte` tag carries its SHA-256
   fingerprint instead, which is enough to check a presented token without keeping it.
3. The token appears nowhere in the state.
4. The five answers establish what `sensitive` protects, what HCP Terraform sends to the
   cloud platform, what verifies it, how long the returned credentials live, and where a
   workspace's credentials are declared.

## The measurement at the heart of the lab

On 2026-09-25, with Terraform 1.16.1, on this very configuration:

| Where | The token |
| --- | --- |
| `terraform show` | `(sensitive value)` |
| `terraform.tfstate` | `"Jeton": "svc-7f3a91c4e2b8-prod"`, **twice** |

`sensitive` acts on what Terraform prints, not on what it records. The same holds for a
saved plan, which carries the value as well.

## How it is proven

The tests apply the configuration **in a run environment they build themselves**: every
`AWS_*` variable of the machine is removed, `HOME` points at an empty directory so no
`~/.aws` can contribute, and the credentials are placed as HCP Terraform places them. A
configuration written to receive its credentials works there; one that contains them works
too, which is precisely why a second check reads the files.

Those two halves are asserted **together**, in one test, and the first cycle says why: when
they were two, the "an instance exists" half was **green before any work**, since the
starting configuration authenticates perfectly with its hardcoded keys. Measured on
2026-09-25: 1/9 without doing anything. Joined, the pair is only reachable once both halves
of the work are done.

Checked by degrading the solution: removing the keys but leaving the token in the tag gives
6/8, and posting the fingerprint while leaving the keys in the provider gives 7/8.
