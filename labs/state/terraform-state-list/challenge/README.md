# 🎯 Challenge: find an address when all you know is the identifier

## ✅ Objective

In `challenge/work`, every file is **complete and applicable** except one:
**`reponses.auto.tfvars`**, which carries five `???`.

Apply first, otherwise there is nothing to look for:

```bash
terraform init
terraform apply
```

Three outputs then publish the **identifier** of a randomly designated instance,
without ever saying which one:

```bash
terraform output id_worker_recherche    # one instance of random_pet.worker  (count = 6)
terraform output id_service_recherche   # one instance of random_pet.service (for_each, 8 keys)
terraform output id_archive_recherche   # one archive of the stockage module (for_each, 5 keys)
```

Fill in the five answers:

1. **`adresse_worker`**: the address of the `random_pet.worker` instance carrying
   `id_worker_recherche`, indexed by **position**.
2. **`adresse_service`**: that of the matching `random_pet.service` instance,
   indexed by **key**.
3. **`adresse_archive`**: that of the matching archive, **qualified by the
   module**.
4. **`adresse_data_module`**: the full address of the data source declared in
   `modules/stockage/`. Careful, it does not start with `data`.
5. **`nombre_managees`**: the number of `mode: managed` instances in the state,
   modules **included**, data sources **excluded**.

Addresses are written exactly as `terraform state list` prints them: brackets,
quotes and module prefix included. Under `zsh`, quote any bracketed address, or
the shell will eat it before Terraform sees it.

## 🔍 Validation

`dsoxlab check state-terraform-state-list` **rebuilds the truth** from
`terraform show -json`, descending recursively into `child_modules`, then resolves
each published identifier to the address carrying it and compares with yours. An
answer right about the resource but wrong about the index, the key or the module
prefix fails.

Also proven, by execution:

- an address **without an index** returns **all** instances of the resource, and a
  **module** address is a valid filter;
- the output order follows **module depth**, not the alphabet;
- the **four** distinct diagnostics of an address matching nothing, all exit
  code 1, whereas an `-id` with no match returns **0** and empty output;
- the `state list | grep -v ^data | wc -l` recipe does return **one more** than
  the real count: it wrongly counts the module's data source;
- `plan -detailed-exitcode` returns 0: reading the state changes nothing.

Stuck? `dsoxlab hint state-terraform-state-list`.
