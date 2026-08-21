# Deux répertoires, deux backends, deux jeux de droits

Séparer `dev` de `prod` par deux répertoires n'est pas une préférence de rangement.
C'est la seule organisation qui permette **deux jeux de credentials** et **deux
états** indépendants, et c'est ce que la documentation recommande explicitement
pour des déploiements distincts : des « separate Terraform configurations that
correspond to architectural boundaries », combinées à des modules réutilisables
pour le code commun.

## L'argument qui compte, et qui n'est pas l'ergonomie

On lit souvent que les **workspaces** sont à éviter parce qu'un
`terraform workspace select` oublié peut détruire le mauvais environnement.
L'argument est vrai mais secondaire. L'argument officiel est **structurel** :

> Workspaces are not appropriate for system decomposition or deployments requiring
> separate credentials and access controls.

La raison tient en une phrase : « CLI workspaces within a working directory use the
**same backend** ». Un seul backend, donc un seul jeu d'accès. Une production qui
doit s'authentifier avec un **rôle** différent de `dev` ne peut donc pas vivre dans
un workspace CLI, quelle que soit la discipline de l'équipe.

## Le montage : un module, deux racines

```text
depot/
├── modules/plaque/       ← le code commun, ecrit UNE fois
├── envs/dev/             ← racine, backend et etat propres
├── envs/prod/            ← racine, backend et etat propres
└── etats/                ← les deux fichiers d'etat
```

Chaque racine appelle le module par un **chemin relatif**, avec ses valeurs :

```hcl
module "plaques" {
  source = "../../modules/plaque"

  environnement = "prod"
  repliques     = 3
}
```

## Pourquoi le bloc `backend` est vide

Le réflexe naturel serait de paramétrer le chemin de l'état par une variable. Il
est **interdit** :

```text
Error: Variables not allowed

  on main.tf line 12, in terraform:
  12:     path = "../etats/${var.env}.tfstate"

Variables may not be used here.
```

« A backend block cannot refer to named values (like input variables, locals, or
data source attributes). » Deux issues s'offrent alors : **dupliquer** le fichier
de backend dans chaque racine, ou employer la **configuration partielle**.

## La configuration partielle, en pratique

Le bloc reste **vide**, donc **identique** partout :

```hcl
terraform {
  backend "local" {}
}
```

Et les arguments manquants sont fournis à l'**initialisation** :

```bash
# dans envs/prod
terraform init -backend-config=backend-prod.hcl
```

```hcl
# envs/prod/backend-prod.hcl
path = "../../etats/prod.tfstate"
```

La documentation en donne trois formes : un **fichier** via
`-backend-config=PATH`, des paires via `-backend-config="KEY=VALUE"`, ou la saisie
**interactive**. C'est le motif le plus employé en automatisation, parce qu'il
garde un code **identique** d'un environnement à l'autre.

Terraform enregistre ensuite la configuration retenue dans
`.terraform/terraform.tfstate` : c'est là qu'on vérifie, sans deviner, quel état
une racine pilote vraiment.

```bash
jq '.backend.config.path' .terraform/terraform.tfstate
```

## Ce que la séparation garantit

Un `terraform destroy` dans `envs/dev` ne peut pas toucher `envs/prod` : la
commande n'agit que sur l'état de sa racine, et les deux états sont distincts. La
propriété se **vérifie**, elle ne se suppose pas :

```bash
cd envs/dev && terraform destroy -auto-approve
cd ../prod && terraform show -json | jq '.values.root_module'
```

Le second doit être **intact**. C'est exactement ce que fait la validation de ce
lab, dans une copie du travail.

## Deux pièges de backend distant

Sur un backend partagé, deux points manquent à beaucoup d'exemples. Le
**verrouillage** d'abord : le backend S3 documente `use_lockfile`, dont la valeur
par défaut est **`false`**, et le verrouillage par DynamoDB est désormais
**déprécié**. Un backend d'équipe sans verrou, c'est deux `apply` simultanés et un
état corrompu.

Le **changement** de backend ensuite : « When you change a backend's configuration,
you must run `terraform init` again ». Terraform propose alors de **migrer**
l'état, ce qui est précisément le passage d'un lab local à un backend distant.

## À vous de jouer

Vous savez pourquoi deux répertoires valent mieux que deux workspaces, pourquoi un
bloc `backend` ne prend pas de variable, comment la configuration partielle règle
le problème, et comment prouver l'isolation. Le challenge vous fait câbler deux
racines sur un module partagé, puis détruire dev pour voir prod tenir.

```bash
dsoxlab run environments-separate-environments
dsoxlab check environments-separate-environments
dsoxlab hint environments-separate-environments
```

Il se joue **hors ligne**, avec le backend `local`.

Sous-objectif d'examen visé : **3b** (backends et configuration partielle).

Référence : [séparer dev, staging et prod](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/separer-environnements/)
