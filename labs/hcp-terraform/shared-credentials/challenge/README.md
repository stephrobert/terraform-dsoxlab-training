# 🎯 Challenge: get the secrets out of the code and out of the state

## 📦 Starting point

`challenge/work` holds two directories. **No account**: a local emulator stands
in for AWS.

| File | State |
| --- | --- |
| `configuration/versions.tf` | provider carrying **two keys in clear text** |
| `configuration/main.tf` | an instance carrying the **token** in a tag |
| `configuration/variables.tf`, `jeton.auto.tfvars` | **supplied**, do not change |
| `questionnaire/questionnaire.tf` | **supplied**, do not change |
| `questionnaire/reponses.auto.tfvars` | five `???` to answer |

## ✅ Objective

1. **Take the credentials out of the provider.** The environment supplies them,
   as HCP Terraform does in a run environment.
2. **Stop writing the token into the instance.** Replace the `Jeton` tag with an
   `Empreinte` tag carrying its SHA-256 fingerprint.
3. **Answer the five questions** on dynamic credentials.

## 🧭 Look before you fix

Apply as-is and look at `terraform.tfstate`. The variable is marked `sensitive`,
`terraform show` prints `(sensitive value)`, and the state holds the token in
clear text, twice.

That is the whole point of this lab, and one of the five questions.

## ⚠️ Removing the keys is only half the work

With no credentials anywhere, the provider answers:

```
Error: No valid credential sources found
```

The configuration must be written to **receive** its credentials, not to work
without any. The tests supply them the way the platform does, in the environment.

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-shared-credentials
```

Eight tests. They apply your configuration in an environment stripped of every
`AWS_*` on the machine, with no `~/.aws`, then sweep the entire state file for
the token — not just the tag you are expected to change, because a secret moved
somewhere else would be just as exposed.

Stuck? `dsoxlab hint hcp-terraform-shared-credentials`.
