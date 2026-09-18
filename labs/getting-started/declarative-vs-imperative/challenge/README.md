# 🎯 Challenge: prove idempotence where the script diverges

## Starting point

`challenge/work` contains four files:

- `imperatif.sh`: **provided, to read, not to fix**. It builds an output
  directory, writes a report in it and records an identifier drawn on every
  call. Replay it twice and compare: the identifier changes, and the report
  grows.
- `versions.tf`: **complete**. It pins `local`, `null` and `random`.
- `main.tf`: **full of holes**. Three resources, including the arguments that
  decide whether generated values are stable or not.
- `outputs.tf`: **full of holes**. Two outputs.

There is no `.terraform/`, no state, no lock file.

## ✅ Objective

Reach the same result as the script in Terraform, then prove what separates
them.

1. **`random_string.identifiant`**: eight characters, no uppercase, no special
   characters, and a `keepers` that makes it **stable**.
2. **`local_file.rapport`**: its content is **built** from the identifier, and
   the file is **replaced**, never piled up.
3. **`null_resource.empreinte`**: its trigger depends on the identifier.
4. **The two outputs**: the identifier, and the report path.

Then, without changing your code: delete the report by hand, observe the drift,
and let Terraform repair it.

## 🧭 What the lab makes you observe

- **Two runs of the script give two identifiers.** Two `apply` of the same code
  give one: the value is remembered in the state.
- **The imperative report grows, the declarative one is replaced.** One
  describes a history, the other a state.
- **After the report is deleted, the plan announces a single create.** The
  identifier is not dropped, and the `null_resource` is not replaced: drift is
  repaired where it happened.
- **The identifier survives the repair.** `keepers` guarantees it, nothing else.

## 🔍 Validation

```bash
dsoxlab check getting-started-declarative-vs-imperative
```

Eight tests reading `terraform show -json`, `output -json`, a plan saved with
`-out` and read back as JSON, and exit codes. The last one compares both
approaches on the same gesture: the replayed script diverges, the replayed
configuration no longer moves. None of them reads your `.tf`.
