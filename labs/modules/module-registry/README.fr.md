# Un module de registre est téléchargé, versionné, et jamais verrouillé

Un module local se lit sur place. Un module de **registre**, lui, est
**téléchargé** dans `.terraform/modules/`, et il porte une **version**. C'est
cette version qui pose le seul vrai problème du sujet : le fichier
`.terraform.lock.hcl`, qui verrouille vos providers, **ne verrouille aucun
module**.

## L'adresse en trois parties

Une source de registre s'écrit `namespace/name/provider`, sans préfixe `./` ni
`../` :

```hcl
module "etiquette" {
  source  = "cloudposse/label/null"
  version = "0.25.0"

  namespace = "demo"
  name      = "ouest"
}
```

Ce format n'est pas arbitraire, il se **déduit** du dépôt publié. La règle de
publication impose un nom en trois morceaux, `terraform-<PROVIDER>-<NAME>` : le
dépôt `cloudposse/terraform-null-label` donne donc l'adresse
`cloudposse/label/null`. Le `<PROVIDER>` n'est pas forcément un cloud, ici c'est
`null`.

## Ce que l'`init` télécharge

```text
Initializing modules...
Downloading registry.terraform.io/cloudposse/label/null 0.25.0 for etiquette...
- etiquette in .terraform/modules/etiquette
```

Le registre des modules enregistre **trois** informations là où un module local
n'en avait que deux :

```json
{
  "Key": "etiquette",
  "Source": "registry.terraform.io/cloudposse/label/null",
  "Version": "0.25.0",
  "Dir": ".terraform/modules/etiquette"
}
```

La clé **`Version`** n'existe **que** pour un module de registre. Et `Dir` pointe
cette fois **sous** `.terraform/`, la copie étant bien réelle : le dossier
téléchargé contient les fichiers du dépôt, `main.tf`, `variables.tf`,
`outputs.tf`, mais aussi son `README.md`, ses `examples/` et son `.git`.

## `version` est facultatif, et c'est un piège

Retirez l'argument `version` : l'`init` **passe quand même**.

```text
Downloading registry.terraform.io/cloudposse/label/null 0.25.0 for etiquette...
```

Terraform a retenu la **plus récente** disponible. Rien ne l'interdit, et c'est
justement ce qui rend l'omission dangereuse : le même code, initialisé demain sur
un autre poste, prendra une **autre** version.

## Le verrou ne couvre pas les modules

C'est le fait le plus mal connu du sujet, et la documentation ne le cache pas :
« At present, the dependency lock file tracks only **provider** dependencies.
Terraform does not remember version selections for remote modules. »

La preuve tient en deux observations. Dans un projet qui déclare un provider, le
verrou ne parle **que** de lui :

```bash
grep -c cloudposse .terraform.lock.hcl
```

```text
0
```

Et dans un projet dont la **seule** dépendance est un module de registre, il n'y
a **pas de fichier de verrouillage du tout**. Rien n'est donc figé côté module,
sauf ce que vous écrivez vous-même dans `version`.

## Pourquoi votre `~> 0.24` reste bloqué

Voici le comportement que personne ne devine, et que tout le monde finit par
rencontrer. Avec une contrainte souple, la version retenue au premier `init`
**reste installée** aux `init` suivants :

```text
$ terraform init          # premier init, contrainte ~> 0.24
Downloading registry.terraform.io/cloudposse/label/null 0.24.1 for etiquette...

$ terraform init          # second init, rien ne bouge
Initializing modules...
```

`modules.json` porte toujours `0.24.1`, alors que `0.25.0` existe et satisfait la
contrainte. La documentation l'explique : « Terraform uses the newest
**installed** version of the module that meets the constraint. » Une seule option
débloque la situation :

```text
$ terraform init -upgrade
Upgrading modules...
Downloading registry.terraform.io/cloudposse/label/null 0.25.0 for etiquette...
```

Notez la nuance : sur un poste **vierge** ou dans une **CI**, aucune copie n'est
installée, donc la plus récente est retenue **sans** `-upgrade`. Le même code
n'installe pas la même version chez vous et dans le pipeline.

## Une contrainte exacte fige aussi vers le bas

Changer la contrainte pour une version **antérieure** ne demande pas `-upgrade` :
la copie installée ne satisfait plus la contrainte, donc Terraform télécharge.

```text
$ terraform init          # la contrainte passe de "0.25.0" a "0.24.1"
Downloading registry.terraform.io/cloudposse/label/null 0.24.1 for etiquette...
```

Retenez la règle sous-jacente : l'`init` **conserve** la copie installée tant
qu'elle satisfait la contrainte, et **télécharge** dès qu'elle ne la satisfait
plus. `-upgrade` force la réévaluation dans tous les cas.

## Le sous-répertoire `//`, et l'ordre qui compte

`//` n'est pas une notion de registre, mais de **paquet** : elle désigne un
sous-répertoire à l'intérieur de ce que Terraform a téléchargé, dépôt Git ou
archive compris. Sur une source Git, elle cohabite avec l'argument `?ref=`, et
l'ordre des deux n'est **pas libre** : « the sub-directory portion must be
**before** those arguments ».

```hcl
# correct
source = "git::https://example.com/reseau.git//modules/vpc?ref=v1.2.0"
```

L'ordre inverse produit une erreur qui nomme le vrai coupable, la révision :

```text
Error: Failed to download module

error downloading '...?ref=0.25.0%2F%2Fexports': invalid ref: "0.25.0//exports"
```

Terraform a pris `0.25.0//exports` pour un nom de révision, ce qu'il n'est pas.

## Ce que `version` ne fait pas

Sur une source **Git**, `version` n'existe pas : c'est `?ref=` qui fige, et il
accepte un tag, une branche ou un commit. Sur une source **locale**, `version`
est carrément refusé, l'`init` s'arrêtant sur `Invalid registry module source
address`. La règle officielle est nette : « You can only use the `version`
argument when the `source` argument points to a module listed in a registry ».

## Prouver la version installée

Deux artefacts, deux informations différentes, et il faut les **deux** :

| Artefact | Ce qu'il donne |
| --- | --- |
| `.terraform/modules/modules.json` | la version **résolue**, réellement installée |
| `terraform show -json <plan>` | la **contrainte** écrite, sous `module_calls.<nom>.version_constraint` |

```bash
terraform plan -out=plan.tfplan
terraform show -json plan.tfplan | jq '.configuration.root_module.module_calls'
```

Une contrainte souple avec une vieille version installée, c'est exactement le cas
que la sortie humaine ne montre pas et que ces deux fichiers exposent.

## À vous de jouer

Vous savez lire l'adresse en trois parties, ce que l'`init` télécharge, pourquoi
le verrou ignore les modules, comment une copie installée survit à une contrainte
souple, et où placer un `//` face à un `?ref=`. Le challenge vous remet trois
projets : un à épingler, un à laisser souple, un à adresser par sous-répertoire.

```bash
dsoxlab run modules-module-registry
dsoxlab check modules-module-registry
dsoxlab hint modules-module-registry
```

Ce lab exige un **accès réseau** à `registry.terraform.io` et à `github.com`.

Sous-objectif d'examen visé : **4b** (utiliser un module), niveau Associate.

Référence : [utiliser un module du registre](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/module-registry/)
