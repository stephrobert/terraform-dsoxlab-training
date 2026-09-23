# Structuring a Terraform project: what matters, and what does not

`main.tf`, `variables.tf`, `outputs.tf`: the convention is everywhere, and it is
useful. But you need to know exactly what it is, because many beginners believe
it affects execution. **It does not, at all.**

## Terraform reads a directory, not files

Terraform loads **every** `.tf` file in a directory and evaluates them as a
single document. File names, their number, their order: none of it has any
functional effect.

Two consequences, opposite and equally important.

**The good one**: you can reorganise freely. Moving a block from one file to
another changes strictly nothing in the plan. It is a risk-free refactoring, and
it is provable.

**The bad one**: a forgotten file still counts. Rename `tout.tf` to
`tout.tf.old` and Terraform ignores it, because the extension is no longer
`.tf`. But leave it as `.tf` next to your new split, and **every block is
declared twice**.

```text
Error: Duplicate variable declaration

  A variable named "projet" was already declared at variables.tf:1,1-19.
```

## The convention, and why it holds

| File | What it carries |
|---|---|
| `terraform.tf` | the `terraform` block: `required_version`, `required_providers` |
| `providers.tf` | the `provider` blocks, their aliases, their regions |
| `variables.tf` | the `variable` blocks |
| `locals.tf` | the `locals` block or blocks |
| `main.tf` | the `resource` and `data` blocks |
| `outputs.tf` | the `output` blocks |

It holds because it answers a reading question: "where is `projet` declared?"
gets answered without a `grep`. On a fifteen-line module it is useless; on a
real project it is what lets somebody else walk into it.

## Proving a split changed nothing

That is the part usually skipped, and the only one that counts:

```bash
terraform plan -out=reference.tfplan
terraform show -json reference.tfplan > plan-reference.json
# ... split ...
terraform plan -out=apres.tfplan
terraform show -json apres.tfplan > plan-apres.json
```

Then compare both `resource_changes`, address by address. A single divergence
means a block was lost or touched during the move.

<Aside type="caution" title="Do not compare the JSON files as they are">
A plan carries a `timestamp` and a `terraform_version` that change between calls
without the configuration moving. Compare `resource_changes`, not whole
documents.
</Aside>

## Value precedence, in the real order

When several sources give a value to the same variable, Terraform applies them
in a fixed order, **from weakest to strongest**:

1. the `default` of the `variable` block;
2. the **`TF_VAR_<name>`** environment variable;
3. the **`terraform.tfvars`** file;
4. the **`terraform.tfvars.json`** file;
5. the **`*.auto.tfvars`** files, loaded in **alphabetical order**;
6. the **`-var`** and **`-var-file`** command-line options.

The rank of `TF_VAR_` is the one almost everyone places too high. An environment
variable **does not win** against a `terraform.tfvars`: it sits just above the
`default`, and below any values file.

```bash
export TF_VAR_projet=depuis-l-environnement
# with projet = "catalogue" in terraform.tfvars
terraform apply
terraform output projet_effectif     # "catalogue"
```

Between two `*.auto.tfvars`, **alphabetical** order decides, not writing order
nor modification date. And the command line always wins.

## Over to you

You now know that file names have no functional effect, that leaving the
monolith in place redeclares everything twice, that a split is proven by
comparing two plans, and that `TF_VAR_` is weaker than a values file.

The challenge has you split a monolith, then produce those proofs.

```bash
dsoxlab run getting-started-terraform-project-structure
dsoxlab check getting-started-terraform-project-structure
dsoxlab hint getting-started-terraform-project-structure
```

Exam sub-objective covered: **2e** (declare and consume variables and outputs,
including value precedence), leaning on **2a**.

Reference: [Structuring a Terraform project](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/structure-projet-terraform/)
