# Scenario: depends_on does not go where a reference suffices

**Exam objective targeted: 2d.**

An attribute reference does not wait for a value to be known: it waits for the upstream resource to have finished being applied. The trap covered here is the comfort `depends_on`, added on top of a reference that already ordered everything, while the project's only genuinely hidden dependency is missing and makes the apply fail.

## Capability targeted

Decide, block by block, between a dependency already expressed by a reference and a hidden one: remove the redundant `depends_on`, replace a hard-coded path with a reference, add the one `depends_on` nothing else can express, and demonstrate the shape of the resulting graph in the JSON plan.

## Where the learner starts

`challenge/work` holds neither state nor `.terraform`:

- `versions.tf`: complete, not to be touched. `required_version = ">= 1.15.0"`, the `hashicorp/local`, `hashicorp/null` and `hashicorp/random` providers pinned.
- `variables.tf`: complete. `racine` (string, default `"livraison"`).
- `main.tf`: four blocks, two of them booby-trapped.
  - `random_pet.nom`: complete.
  - `local_file.manifeste`: writes `${var.racine}/manifeste.json`, its `content` is a `jsonencode` referencing `random_pet.nom.id`, and it also carries `depends_on = [random_pet.nom]`. The reference and the `depends_on` say the same thing, one of the two is surplus.
  - `null_resource.socle`: complete, not to be touched. Its `local-exec` creates the directory, waits two seconds, then writes the `.pret` marker into it. It simulates a service that takes time to become operational and exposes no usable attribute.
  - `null_resource.publication`: its `local-exec` checks for `.pret` then copies the manifest to `publie.json`, with both paths hard-coded, and with no `depends_on` at all.
- `data.tf`: `data "local_file" "publie"` reads `${var.racine}/publie.json` through a literal path, its `depends_on` is holed with `???`.
- `outputs.tf`: `nom_livraison` and `taille_publie` started, values holed.

The brief requires an `init` then an `apply` before any modification. The starting observation is a double failure, verified on Terraform 1.15.4: first syntax errors on the `???` in `data.tf` and `outputs.tf`; then, once those holes are filled but while `publication` is not wired to the platform, the reproducible provisioner failure, `Error running command 'test -f livraison/.pret && cp ...': exit status 1`. Terraform launched `publication` in parallel with the platform, because no line of code linked the two.

## The state to reach

1. A full `apply` goes through end to end, and `livraison/publie.json` exists with exactly the content of `livraison/manifeste.json`.
2. `local_file.manifeste` carries no `depends_on` any more: the order with `random_pet.nom` holds through the reference already present in `content`.
3. `null_resource.publication`'s command no longer contains the manifest's path hard-coded: it interpolates `local_file.manifeste.filename`. The dependency becomes implicit, as the documentation recommends as soon as upstream data is usable.
4. `null_resource.publication` carries `depends_on = [null_resource.socle]`, and nothing else: it is the project's only dependency no reference can express, since `null_resource` exposes no useful data.
5. `data.local_file.publie` carries `depends_on = [null_resource.publication]`: its arguments are literal, and nothing would otherwise indicate it must wait for the copy.
6. The outputs are wired: `nom_livraison` is the `random_pet`'s `id`, `taille_publie` the length of the content read by the data source.
7. No block in the configuration declares in `depends_on` a resource it already references elsewhere.
8. A `plan` right after the final apply proposes nothing.

## How it is proven

The tests drive Terraform and never read the `.tf` files.

- `terraform plan -out=tfplan` then `terraform show -json tfplan`, section `configuration.root_module.resources`: `local_file.manifeste` no longer has a `depends_on` key, and its `expressions.content.references` contain `random_pet.nom.id`. The order is therefore still guaranteed, without the duplicate.
- Same section, `null_resource.publication`: `depends_on == ["null_resource.socle"]` strictly, and `provisioners[0].expressions.command.references` contains `local_file.manifeste.filename`. One explicit dependency, one implicit, each on the right neighbour.
- Same section, `data.local_file.publie`: `depends_on` contains `null_resource.publication`.
- A cross-cutting rule over the whole configuration: for each block, the intersection between its `depends_on` and the addresses quoted in its `references` must be empty. That is the test refusing the comfort `depends_on`, wherever the learner puts it.
- A cold plan, after `destroy`: `resource_changes` holds an entry at address `data.local_file.publie`, `mode: "data"`, `actions: ["read"]`. The read was pushed back to apply time, which proves the data source's `depends_on` is really wired and not merely written.
- System state after the apply: `livraison/publie.json` exists and its content is identical to that of `livraison/manifeste.json`, which is only reachable if the copy happened after the platform and after the manifest was written.
- `terraform output -json`: `nom_livraison` is a non-empty string, `taille_publie` a strictly positive integer equal to the manifest's size.
- `terraform plan -detailed-exitcode`: code 0 right after the final apply.

None of these checks passes on an empty directory, nor on the starting configuration, whose apply stops in error.

Reference: https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/depends-on/
