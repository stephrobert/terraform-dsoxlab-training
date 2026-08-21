# La structure standard d'un module, et le seul nom de fichier qui compte

Terraform charge **tous** les `.tf` d'un répertoire et les traite comme un seul
document. Découper en `main.tf`, `variables.tf` et `outputs.tf` ne change donc
rien au résultat : c'est une convention **de lecture**.

Sauf pour une famille de noms, `override.tf` et `*_override.tf`, que Terraform
charge **en dernier** et qui **écrasent** ce qui précède. Ce tutoriel montre la
structure attendue par l'écosystème, puis cette exception, mesurée.

## Ce que la documentation appelle la Standard Module Structure

Elle existe, elle a une page officielle, et l'outillage s'appuie dessus : « We
recommend a common repository structure [...] Terraform tooling is built to
understand the standard module structure and use that structure to generate
documentation, index modules for the module registry, and more. »

Le socle minimal officiel tient en **quatre fichiers** :

```text
minimal-module/
├── README.md
├── main.tf
├── variables.tf
└── outputs.tf
```

Trois remarques que l'on rate souvent :

- **`README.md` fait partie du minimum**, pas des options. Et il n'a pas à
  documenter les entrées et les sorties : « The README doesn't need to document
  inputs or outputs of the module because tooling will automatically generate
  this. »
- **`LICENSE` est au même niveau** : « many organizations will not adopt a module
  unless a clear license is present. We recommend always having a license file,
  even if it is not an open source license. »
- Le bloc `terraform` ne fait **pas** partie de ce socle. Le style guide lui
  donne un fichier à part : « A `terraform.tf` file that contains a single
  `terraform` block which defines your `required_version` and
  `required_providers` ».

## Les modules imbriqués, et l'appel par chemin relatif

Un module peut en contenir d'autres, sous `modules/`. La documentation y attache
une règle de visibilité qui tient au **README** :

> Any nested module with a `README.md` is considered usable by an external user.
> If a README doesn't exist, it is considered for internal use only.

Un sous-module sans README est donc **interne**, et cette distinction n'est
inscrite nulle part ailleurs que dans la présence du fichier.

L'appel se fait par un **chemin relatif** :

```hcl
module "carte" {
  source   = "./modules/carte"
  for_each = var.zones

  zone = each.key
}
```

La raison est technique : « they should use relative paths like
`./modules/consul-cluster` so that Terraform will consider them to be part of
the same repository or package, rather than downloading them again separately ».
Le JSON du plan permet de le vérifier :

```bash
terraform plan -out=p.tfplan
terraform show -json p.tfplan | jq '.configuration.root_module.module_calls.carte.source'
```

```json
"./modules/carte"
```

## Le répertoire `examples/`

La doc attend des exemples autonomes : « Examples of using the module should
exist under the `examples/` subdirectory at the root of the repository. » Ils se
valident indépendamment de la racine :

```bash
terraform -chdir=examples/minimal init
terraform -chdir=examples/minimal validate -json
```

```json
{"valid": true, "error_count": 0}
```

Un détail compte pour un module publié : dans un exemple, « any `module` blocks
should have their `source` set to the address an external caller would use, not
to a relative path », puisque ces exemples finissent copiés ailleurs.

## Un `type` sur chaque output

Le style guide de la 1.15 aligne les sorties sur les variables : « Like you would
for variables, provide a `type` and `description` for each output », dans l'ordre
`Type, Description, Value, Sensitive`.

```hcl
output "emplacements" {
  type        = map(string)
  description = "Chemin de la carte, par zone."
  value       = { for nom, instance in module.carte : nom => instance.emplacement }
}
```

Le type déclaré ressort tel quel dans la sortie machine :

```bash
terraform output -json | jq '.emplacements.type'
```

```json
["map", "string"]
```

## L'exception : `override.tf`

Voici le seul endroit où le **nom du fichier** change le résultat. Prenons une
ressource déclarée dans `main.tf` :

```hcl
resource "local_file" "registre" {
  filename        = "${path.root}/registre.txt"
  content         = "registre des cartes\n"
  file_permission = "0644"
}
```

Ajoutez un `override.tf` qui **redéclare la même ressource**, avec un seul
attribut :

```hcl
resource "local_file" "registre" {
  file_permission = "0600"
}
```

Terraform **fusionne** les deux, et le second gagne :

```bash
terraform apply -auto-approve
terraform show -json | jq '.values.root_module.resources[]
  | select(.address == "local_file.registre") | .values.file_permission'
```

```json
"0600"
```

Le fichier sur le disque porte bien `600`. La documentation le formule ainsi :
« Terraform loads this and all files ending with `_override.tf` last. »

**Changez le nom du fichier, et tout s'effondre.** Le même contenu dans un
`surcharge.tf` produit :

```text
Error: Duplicate resource "local_file" configuration

  on surcharge.tf line 1:
   1: resource "local_file" "registre" {

A local_file resource named "registre" was already declared at
main.tf:8,1-33. Resource names must be unique per type in each module.
```

C'est la démonstration en une commande : les noms de fichiers sont cosmétiques,
**sauf ceux-là**. La documentation met d'ailleurs en garde contre leur usage
courant, parce qu'ils rendent une configuration difficile à lire : on les réserve
aux cas où l'on ne peut pas modifier le fichier d'origine.

## À vous de jouer

Vous savez ce que contient la structure standard, pourquoi le `README` d'un
sous-module décide de sa visibilité, pourquoi l'appel se fait par chemin relatif,
ce qu'un `type` sur un output change dans la sortie machine, et ce que
`override.tf` a de particulier. Le challenge vous remet un fichier unique où tout
est empilé, à éclater proprement.

```bash
dsoxlab run modules-module-structure
dsoxlab check modules-module-structure
dsoxlab hint modules-module-structure
```

Sous-objectif d'examen visé : **4a** (écrire et utiliser des modules), niveau
Associate et Professional.

Référence : [structure standard d'un module](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/structure-module/)
