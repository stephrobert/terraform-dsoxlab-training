# 🎯 Challenge: rank fifteen sources, and hold on unseen cases

## 📦 Starting point

`challenge/work` holds a configuration that already applies, with no remote
infrastructure. **No HCP Terraform account is required.**

| File | State |
| --- | --- |
| `VOCABULAIRE.md` | the fifteen accepted identifiers, **shuffled** |
| `variables.tf`, `versions.tf`, `cas.auto.tfvars` | **supplied** |
| `precedence.tf` | eleven `???` out of fifteen entries, four **anchors** |
| `resolution.tf` | the resolution and the lexical duel, to be written |
| `qcm.tf` | five statements to settle |

The four anchors (`cli_var`, `tf_var_env`, `workspace`, `terraform_tfvars`)
prevent guessing the table by rotating it one notch.

## ✅ Objective

1. **The complete table**, most to least prioritary.
2. **The resolution**: for each case, the retained source **and** its value.
3. **A case with no source** resolves to the sentinel, never to `null` nor to a
   plan error.
4. **The lexical duel**: separate two identical sets by code points.
5. **The five statements**, as booleans.

## 🧭 The inversion, and that is the whole subject

Among **normal** variable sets, the **narrowest** scope wins.
Among **priority** ones, it is the **broadest**.

> When a variable set is priority, the values take precedence over any variables
> with the same key set at a more specific scope.

And two more surprises: the files are at the **bottom** of the table, and an HCL
map **has no order** — the name decides, not the writing order.

## ⚠️ A case-by-case resolution will not pass

The six supplied cases can be resolved by hand. The tests generate **eight
more**, which you will not see, two aimed at the inversion and one empty.

Walk `local.ordre`. Name no case.

## 🔍 Validation

```bash
dsoxlab check hcp-terraform-variable-sets
```

Twelve tests. The table is compared **position by position**, and the message
names the offending rank. No test reads your `.tf` or `.tfvars`.

Stuck? `dsoxlab hint hcp-terraform-variable-sets`.
