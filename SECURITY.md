# Security policy

**Language:** [English](./SECURITY.md) · [Français](./SECURITY.fr.md)

## Supported versions

`terraform-dsoxlab-training` is under active development. Security fixes
are applied to the latest version of the `main` branch.

| Version | Supported |
| --- | --- |
| latest (`main`) | yes |
| older | no |

## Reporting a vulnerability

**Do not open a public issue for a security vulnerability.**

If you believe you have found one, report it privately:

- Preferred: open a
  [private security advisory](https://github.com/stephrobert/terraform-dsoxlab-training/security/advisories/new)
  on GitHub.
- Otherwise, use the contact details published on
  <https://blog.stephane-robert.info>.

Please include:

- a description of the vulnerability and its impact,
- the steps to reproduce it (command, environment, `terraform version`,
  `dsoxlab --version`),
- any relevant logs or proof of concept.

We will keep you posted on the fix and credit you in the release notes if you
wish.

## Disclosure policy

We practise coordinated disclosure and commit to the following timelines,
counted from the moment we receive your report:

| Step | Target |
| --- | --- |
| Acknowledging your report | within **48 hours** |
| Initial assessment and severity triage | within **5 days** |
| Fix released, or a written remediation plan | within **30 days** |
| Public disclosure of the vulnerability | within **90 days** |

We publish the advisory as soon as a fix is available, or at the **90-day** mark
at the latest, whichever comes first. If a vulnerability is being actively
exploited, we may disclose sooner to protect users. If a complex fix needs more
time, we tell you before the deadline and agree a new date with you, rather than
letting it lapse in silence.

## Scope

This repository ships **lab content**: Terraform configurations, fixtures,
pytest tests and encrypted reference solutions, executed by the external
`dsoxlab` CLI on the learner's own machine.

In scope:

- dangerous or malicious lab material, in particular a configuration that would
  provision resources outside the local emulator or the account the learner
  declared;
- a leaked secret, private key or API token committed by mistake.
  `tests/test_aucun_jeton_versionne.py` rejects those three shapes, and a way
  around that check is itself a vulnerability;
- a reference solution shipped in clear text, which spoils the lab and stays in
  the history.

Out of scope:

- vulnerabilities in the `dsoxlab` engine itself, which belong to
  [its own repository](https://github.com/stephrobert/dsoxlab);
- those of Terraform providers, of the Floci emulator, or of any third-party
  dependency, to be reported to their respective projects;
- a lab that fails or scores badly: that is a defect, and it goes in a public
  issue.

## What this repository will never ask of you

No lab requires a real secret. The AWS section targets the local Floci emulator,
with no account and no card. A single optional lab asks for an HCP Terraform
token: it lives on your machine, never leaves it, and `docs/hcp-token.md`
explains how to place and revoke it.
