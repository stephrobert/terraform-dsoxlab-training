# Make fmt, validate and the outputs agree

A lab checking that commands were typed would prove nothing. What can be proven
is that a **non-interactive chain** goes through the configuration without a
human having to read a single output formatted for them.

That is exactly what a CI does, and it is where the Terraform CLI reveals it has
two faces: the one it shows on screen, and the one it keeps for scripts.

## Every useful command has a machine mode

| Command | Output for a human | Output for a script |
| --- | --- | --- |
| `fmt` | the list of files | the **exit code** |
| `validate` | a boxed text | `validate -json` |
| `plan` | a coloured diff | `plan -out` then `show -json` |
| `output` | `key = value` | `output -json` |
| `show` | a readable state | `show -json` |

The general rule: **never parse what was written to be read**. Text changes
between versions, colour disappears when output is not a terminal, and tables
realign. JSON and exit codes do not.

## `validate -json` answers in structure

```console
$ terraform validate -json | jq '{valid, error_count, warning_count}'
{
  "valid": false,
  "error_count": 1,
  "warning_count": 0
}
```

Two useful things here. First, `valid` is a boolean, not a sentence to
recognise. Second, **warnings are counted separately**: a configuration can be
valid and carry warnings, and it is up to your script to decide whether it
tolerates them.

And the prerequisite people forget: `validate` needs the providers' **schemas**.
Run before `init`, it fails for a reason unrelated to code quality.

## Outputs are the only official channel towards a script

A value not exposed as an `output` is not reachable from outside, short of
digging into state, which amounts to depending on an internal format.

```console
$ terraform output -json | jq -r '.adresse.value'
```

That is the contract: the configuration decides what it publishes, and the script
reads only that.

## `terraform console` works without a terminal

Little known and valuable: the console accepts an expression on its **standard
input** and returns the result, with no interactive session.

```console
$ echo 'cidrhost("10.0.0.0/16", 5)' | terraform console
"10.0.0.5"
```

That lets you check an HCL expression inside a script, or understand what a
function does without writing a throwaway file.

## Do not confuse `plan`'s exit codes

```bash
terraform plan -detailed-exitcode
```

| Code | What it says |
| --- | --- |
| **0** | no changes |
| **1** | error |
| **2** | changes are pending |

Without `-detailed-exitcode`, a plan with changes returns **0** just like an
empty one: the command succeeded, that is all. That flag is what turns `plan`
into a test.

## Over to you

```bash
dsoxlab run getting-started-cli-terraform
dsoxlab check getting-started-cli-terraform
dsoxlab hint getting-started-cli-terraform
```

The lab runs **offline**, on the `local`, `null` and `random` providers. Three
defects are placed deliberately: a file outside canonical format, a validation
error, and missing outputs. Everything must then run **without interactive
confirmation**.

Exam objective targeted: **3c**, run the Terraform workflow in automation.

Reference: [the Terraform CLI](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/cli-terraform/)
