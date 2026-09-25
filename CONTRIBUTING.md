# Contributing to terraform-training

**Language:** [English](./CONTRIBUTING.md) · [Français](./CONTRIBUTING.fr.md)

This repository is a **lab catalog** consumed by the
[`dsoxlab`](https://github.com/stephrobert/dsoxlab) CLI. Contributions are new
labs, fixes and translations. The CLI lives in its own repository: do not add
engine code here.

## Setup

```bash
uv tool install dsoxlab        # the CLI (external tool)
git clone https://github.com/stephrobert/terraform-training.git
cd terraform-training
dsoxlab validate-structure     # check the contract
```

No VM, no `dsoxlab provision`: unlike the Ansible and Linux catalogs, Terraform
runs on the learner's own machine. Every lab is `runtime: shell`.

## The golden rule: a lab is proven in both directions

A passing test proves nothing until you have seen the right thing **fail**.
Before committing a lab:

```bash
dsoxlab run   <id>    # the starting state is in place
dsoxlab check <id>    # MUST fail: the work has not been done
# then apply the reference solution
dsoxlab check <id>    # MUST pass: 100/100
```

A lab whose tests pass **before** the work measures nothing. That is the most
expensive defect in this domain, and the only way to see it is to look.

Ask yourself, for every test: **would it be green if the learner did nothing?**
If yes, it is not a test, it is an assumption about the setup. The fix is to
merge that half into the final test, where it can only be reached after the
work.

## What the tests must read

The state the configuration **computes**, never what a file contains:

```python
# NO: we re-read what the learner wrote
assert "aws_instance" in open("main.tf").read()

# YES: we read what Terraform produced
etat = show_json(WORKDIR)
assert [r["address"] for r in ressources(etat)] == ["aws_instance.web"]
```

`terraform output -json` and `terraform show -json` are the two doors. Reading a
`.tf` file is a last resort, and it has to be justified in the test: some facts
(a provider that carries its credentials, a `cloud` block that cannot be
initialized without an account) leave no trace in any state.

## Anatomy of a lab

```text
labs/<section>/<lab>/
├── lab.yaml            # the contract (id, level, runtime, fixtures, validation…)
├── lab.fr.yaml         # French override of title/description ONLY
├── README.md / README.fr.md        # the lesson
├── scenario.md / scenario.fr.md    # the situation, the target state, the proof
├── fixtures/           # the starting material, copied into challenge/work
└── challenge/
    ├── README.md / README.fr.md    # the mission, no step-by-step
    ├── hints.yaml                  # base64 hints, three cost levels
    └── tests/test_functional.py    # the proof
solution/<section>/<lab>/           # reference solution, encrypted with ansible-vault
```

There is no `setup.yaml` or `cleanup.yaml` here: `runtime.fixtures` declares
what gets copied, and `dsoxlab clean` removes the work directory. A lab that
needs a service (the AWS section uses the Floci emulator) declares it under
`runtime.services`, and dsoxlab starts it.

## Proposing a lab

- **Start from a capability, not from a guide.** Describe something
  demonstrable ("import an existing resource and reconcile drift without
  recreating it"), open an issue, and agree the scope before writing.
- **Point `doc_url` at the real guide** the lab puts into practice. A lab with
  no companion guide teaches instead of proving, which is the site's job.
- **Use current versions.** Pin them, and date the measurement in a comment: a
  catalog that teaches a deprecated argument is worse than one that says
  nothing.

## Local checks before opening a PR

```bash
dsoxlab validate-structure        # the meta.yml + lab.yaml contract
dsoxlab check <lab-id>            # the lab's own tests
python3 -m pytest tests/ -q       # the repository's meta-tests
python3 scripts/gen_catalog.py    # refresh the README catalog
```

The catalog is generated from the real `lab.yaml` files: run
`gen_catalog.py` after adding or renaming a lab, and `--check` to verify.

## Conventions

- **Lab id:** `<section>-<slug>`, matching the directory name.
- **Commits:** in French, a factual subject saying **what changed and why**, no
  conventional prefix. The body says what was measured, including the
  measurements thrown away along the way — they are often worth more than the
  result.
- **i18n:** the unsuffixed file is English (the repository's official language),
  `*.fr.md` is the French translation. Both must say the same thing.
- **Style:** no emoji and no em dash in what the learner reads. Assertion
  messages teach: they say what is wrong and why, not just what was expected.

## Pull requests

Work on a dedicated branch, keep `dsoxlab validate-structure` green, write a
clear description, and link the capability or issue it addresses.
