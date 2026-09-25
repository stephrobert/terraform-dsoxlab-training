# 🎯 Challenge: the compliance audit

## 📦 Starting point

`challenge/work` holds three directories. **No HCP Terraform account.**

| File | State |
| --- | --- |
| `audit/situations.auto.tfvars.json` | **supplied**, seven runs described |
| `audit/variables.tf`, `audit/versions.tf` | **supplied** |
| `audit/verdicts.tf` | one `???`: each situation's verdict |
| `audit/gouvernance.tf` | three `???`: facts to establish |
| `rattachement/versions.tf` | the `cloud` block is missing |
| `secret/main.tf` | two `???`: the sheet and its fingerprint |
| `secret/variables.tf`, `jeton.auto.tfvars` | **supplied**, do not change |

## ✅ Objective

1. **Qualify the seven situations.** Seven words are possible; six are enough, and
   each is used exactly once.
2. **Establish three governance facts.**
3. **Attach `rattachement/`** to the `audit-conformite` workspace of the
   `atelier-dsoxlab` organization, by name.
4. **Write the service sheet** without the token entering the state.

Write a **rule**, not a list of answers: no situation key should appear in your
expression.

## 🧭 The rules do not commute

Every situation crosses two sub-objectives. The order in which you ask the
questions decides the outcome, because each one makes the next moot: a workspace
that runs nothing evaluates no policy; a run that can never apply has nothing to
block; a plan with no changes applies nothing.

## ⚠️ Six different outcomes

That is how the capstone is built, and a test checks it. Two situations receiving
the same verdict would signal a rule that confuses them, not two cases that
happen to look alike.

## 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone6-hcp
```

Eight tests. The audit is read from `terraform output -json`, the attachment from
the initialization output, and the secret from the state, swept in full.

Stuck? `dsoxlab hint certifications-professional-capstone6-hcp`.
