# 🎯 Challenge: work out what six teams may actually do

## 📦 Starting point

`challenge/work` holds two directories. **No account needed.**

| File | State |
| --- | --- |
| `acces/equipes.auto.tfvars.json` | **supplied**, six teams described |
| `acces/variables.tf`, `acces/versions.tf` | **supplied** |
| `acces/acces.tf` | two `???`, with the scale and equivalences supplied |
| `questionnaire/questionnaire.tf` | **supplied**, do not change |
| `questionnaire/reponses.auto.tfvars` | five `???` to answer |

## ✅ Objective

1. **Compute each team's effective access** on the workspace, from what it holds
   at organization, project and workspace level.
2. **List the teams that can apply.** Applying takes at least write access.
3. **Answer the five questions.**

Write a **rule**, not a list of answers: no team key should appear in your
expression, and a seventh team must be handled without rewriting anything.

## 🧭 The trap, and it is a solid habit

Everywhere else, the permission set at the most specific level wins. Here,
permissions **add up**, and the effective access is the **most permissive** of
the three levels — whoever granted it.

Two cases in the file are the documentation's own examples, one in each
direction. If your rule gets both right, it is almost certainly the right rule.

Careful with the other over-correction: nothing accumulates. Two read-level
grants do not make a write.

## ⚠️ The two scales are not the same one

| Scope | Roles |
| --- | --- |
| workspace | `Read` < `Plan` < `Write` < `Admin` |
| project | `Read` < `Write` < `Maintain` < `Admin` |

`plan` exists only on workspaces, `maintenance` only on projects, and it sits
above write. The supplied scale already merges both; use it rather than
comparing by eye.

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-projects-teams
```

Thirteen tests, all reading `terraform output -json`: what your configuration
**computes**, never what it contains.

Stuck? `dsoxlab hint hcp-terraform-projects-teams`.
