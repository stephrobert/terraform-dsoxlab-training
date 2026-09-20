# 🎯 Challenge: classify a plan before applying it

## Starting point

`challenge/work` holds three files, **all provided**:

- `versions.tf`: pins `local`, `null` and `random`.
- `main.tf`: **five resources**, a single `etiquette` variable. They do not all
  react the same way to a change of that variable.
- `terraform.tfvars`: sets `etiquette = "v1"`.

The directory is not initialised and there is no state.

## ✅ Objective

1. **Lay down the reference state**: initialise and apply the configuration as
   is.
2. **Change the value**: move `etiquette` to `"v2"` in `terraform.tfvars`.
3. **Save the plan** in a file named `tfplan`, with
   `terraform plan -out=tfplan`.
4. **Convert it** to `plan.json`, with `terraform show -json tfplan`.
5. **Classify** every changing address in an `analyse.json` file:

   ```json
   {
     "mise_a_jour_en_place": ["..."],
     "remplacement": ["..."]
   }
   ```

6. **Apply that plan**, with `terraform apply tfplan`. No re-plan, no
   interactive confirmation.

## 🧭 What the lab makes you observe

- **Only one of the five resources is updated in place.** The other four depend
  on the label through an argument that forces a replacement:
  `triggers_replace`, a file content, `keepers`, `triggers`.
- **`local_file` never updates.** With that provider everything forces a
  replacement, down to the file permissions.
- **The order of actions varies, the meaning does not.**
  `["delete", "create"]` and `["create", "delete"]` mean the same replacement,
  the second one with `create_before_destroy`.
- **An applied plan becomes stale.** Replay `terraform apply tfplan` and
  Terraform refuses: that is the proof it was consumed.
- **A replacement does not know its future identifier.** It is marked unknown in
  the plan, where an update in place keeps its own.

## 🔍 Validation

```bash
dsoxlab check getting-started-terraform-workflow
```

Eight tests. The saved plan is reopened **by the tool**: a hand-made `tfplan`
does not pass. The truth is never taken from your `analyse.json`: it is
recomputed from the plan actions, then compared to your classification, address
by address. No test reads your `.tf`.
