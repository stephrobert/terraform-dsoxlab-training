# Scenario: take over an existing EC2, rename it, accept its drift

**Exam objective targeted: 1e (manage state, import resources, reconcile drift).**

This lab covers the three traps reading a tutorial never reveals: a `moved` you
believe went through although it was never applied, a `moved` whose `from`
address is wrong and which Terraform ignores **in silence**, and drift you
overwrite by reflex instead of deciding what to do with it.

## Capability targeted

Bring under Terraform's control an EC2 instance created outside it, change its
logical address without the real object being recreated, then reconcile drift by
**accepting** reality, that is, by aligning the code with it rather than the
opposite.

## Where the learner starts

Floci runs locally on `localhost:14566` (Docker socket mounted, `-u root`). The
setup step created, **through the AWS CLI and not through Terraform**, an EC2
instance tagged `Name = legacy-billing-api` and `Owner = finops`. Its id is
dropped in `challenge/work/existing-instance.txt`.

Inside `challenge/work`: a **complete** `providers.tf` (an `aws` provider aiming
at Floci through an `endpoints` block, fake credentials,
`skip_credentials_validation`, `skip_requesting_account_id`,
`skip_metadata_api_check`), an `imports.tf` whose `import` block is holed
(`to = ???`, `id = ???`), **no `resource` block** (it is to be produced, not
copied), and no state.

## The state to reach

1. The instance appears in state with **the id already present in
   `existing-instance.txt`**: it was imported, not recreated.
2. Right after the import, the configuration is **faithful**: an ordinary plan
   proposes nothing. That is the real success criterion for an import, and the
   trap of automatic configuration generation, which produces extra arguments
   that must be removed.
3. The address in state is `aws_instance.billing_api`, although the import was
   done under another name, and the object's id **has not moved**: the rename
   went through a `moved` that was actually **applied**, a `plan` alone writing
   nothing to state.
4. The `moved` block is **still present** at the end of the lab. Removing it is a
   breaking change for anyone still starting from the old address.
5. The `Owner` tag was changed outside Terraform and the learner **accepts** that
   drift: on the Floci side the tag keeps its manual value, state reflects it,
   and so does the code. Both stopping criteria fall together: no drift left to
   reconcile, no change left to apply.
6. No extra instance exists on the Floci side: no destroy, no create.

## How it is proven

The tests query structured state, never the learner's `.tf` file:

- `terraform show -json`: one resource in `mode: managed` at address
  `aws_instance.billing_api`, whose `values.id` **equals** the id read from
  `existing-instance.txt`. Proof of the import and of the absence of recreation.
- `terraform plan -detailed-exitcode` exits **0**, and
  `terraform plan -refresh-only -detailed-exitcode` exits **0** as well. The
  first proves reality matches the code, the second that state matches reality.
- The AWS CLI pointed at Floci shows the `Owner` tag at its **manual** value, and
  returns a single non-terminated instance: drift was accepted and the code
  aligned, without recreation.
- Proof of the `moved`: the test copies the working directory aside, rewrites the
  address in the copied state back to its old name, runs `terraform plan -out`
  and reads the plan as JSON. It requires an entry carrying `previous_address`
  with `actions: ["no-op"]`. A deleted `moved`, or one whose `from` is wrong,
  would produce a `create`, without the slightest error.
