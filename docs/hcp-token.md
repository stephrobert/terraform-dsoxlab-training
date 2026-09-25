# The HCP Terraform token: create it, place it, check it

## First: you do not need one

**None of the seven `hcp-terraform` labs requires an account or a token.** They
deliberately stop just short of authentication, and that is what makes them
verifiable anywhere:

```
Initializing HCP Terraform...

Error: Required token could not be found
```

In the `hcp-workspaces` lab that error is the goal, not a failure: it means your
`cloud` block was accepted. A faulty configuration never gets that far.

This guide is for **going further**: running real remote runs, and playing the
optional lab that uses them.

## Create the token

The simplest way, and it writes the file for you:

```bash
terraform login
```

The command opens your browser, asks you to confirm, then writes
`~/.terraform.d/credentials.tfrc.json`.

By hand, if you prefer: on `app.terraform.io`, your avatar → **User settings** →
**Tokens** → *Create an API token*. Give it a description that says where it
lives, such as `training-workstation`, and an expiry.

Three scopes exist, and they are not interchangeable:

| Scope | What it allows | For what |
| --- | --- | --- |
| **user** | everything you can do | a workstation |
| **team** | what the team can do | a CI pipeline |
| **organization** | manage the organization, not the workspaces | admin tooling |

For this training, a **user** token is the right one.

## Where to put it, and which one wins

Three places, and **the order matters**:

| Priority | Location | Scope |
| --- | --- | --- |
| 1 | `TF_TOKEN_app_terraform_io` | the current session |
| 2 | `TF_CLI_CONFIG_FILE`, when set | whatever that file declares |
| 3 | `~/.terraform.d/credentials.tfrc.json` | the machine |

The environment variable is `TF_TOKEN_` followed by the hostname with its dots
turned into underscores: `app.terraform.io` gives `TF_TOKEN_app_terraform_io`.

```bash
export TF_TOKEN_app_terraform_io=<your-token>
```

And the file takes exactly this shape:

```json
{
  "credentials": {
    "app.terraform.io": {
      "token": "<your-token>"
    }
  }
}
```

### The trap, measured

On 2026-09-25, with Terraform 1.16.1, on one correct configuration:

| What is in place | What Terraform does |
| --- | --- |
| the credentials file alone | it uses the file's token |
| `TF_CLI_CONFIG_FILE` pointing at an empty file | `Required token could not be found` |
| ... **and** `TF_TOKEN_app_terraform_io` set | it uses the variable's token |

In other words: **an environment variable beats the file**, even when you took
care to neutralise the file. That is the most common cause of "I did update my
token and nothing changed": the token you updated is not the one Terraform reads.

## Check rather than assume

```bash
python3 scripts/diagnostic-jeton-hcp.py              # where the token is
python3 scripts/diagnostic-jeton-hcp.py --verifier   # + the API says if it is accepted
```

The script looks at every location, **says which one wins**, flags those holding
a token that is being ignored, and never prints a token's value — only its length
and a truncated fingerprint. Exit codes: `0` a token is in place, `1` no token,
`2` a token the API refuses.

A refused token gives `401 unauthorized`, and the API answers exactly the same
when no token is sent at all: that code does not tell "no token" from "wrong
token", which the diagnostic settles for you by looking at what it found locally.

## What not to do

- **Never commit a token.** Not in a `.tf`, not in a `.tfvars`, not in a
  credentials file dropped into a repository. A meta-test in this catalog rejects
  any file carrying one.
- **Do not pass it as a Terraform variable.** The `shared-credentials` lab
  measures it: a variable marked `sensitive` is not displayed, and its value ends
  up **in clear text in the state**.
- **Do not share it**, not even to help someone debug: a user token carries all
  of your rights.

## Revoke it

On `app.terraform.io`, **User settings** → **Tokens** → the bin. Revocation is
immediate, and it is the right reflex at the slightest doubt: creating another
one takes ten seconds.

```bash
terraform logout    # removes the token from the local file, without revoking it
```

The two are separate actions, and you often need both.
