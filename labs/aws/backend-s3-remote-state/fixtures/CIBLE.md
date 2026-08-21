# Un state distant, verrouille, et lu par une autre stack

Deux croyances font tomber les candidats sur cet objectif :

- que declarer un `backend "s3"` suffit a **verrouiller** le state. Le
  verrouillage est un **opt-in** : `use_lockfile` vaut `false` par defaut ;
- qu'un bloc `backend` se parametre par des variables comme le reste du HCL.

Ce lab fait echouer les deux, puis les repare.

## L'emulateur

Floci tourne en conteneur et fournit S3 sur **`http://localhost:14566`**.
`dsoxlab run` et `dsoxlab check` le demarrent tout seuls : vous n'avez rien a
lancer.

## Les trois repertoires

| Repertoire | Ce que c'est |
| --- | --- |
| `bootstrap/` | **complet**, a appliquer tel quel. Cree le bucket, active le versioning, bloque l'acces public. Son state reste **local**, par necessite |
| `producer/` | un `random_pet` et trois outputs ecrits. Son bloc `terraform {}` est **piege** |
| `consumer/` | un bloc `data "terraform_remote_state"` **troue**, et quatre outputs deja ecrits |

Un fichier `producer/floci.s3.tfbackend` est fourni **a moitie rempli**.

## L'etat a atteindre

| Point | Attendu |
| --- | --- |
| 1 | Le bucket existe sur Floci, versioning actif, acces public bloque |
| 2 | Le bloc `backend "s3"` du producer ne reference plus **aucune** valeur nommee |
| 3 | Le producer n'a **plus aucun** `terraform.tfstate` local, et l'objet existe dans le bucket |
| 4 | La configuration retenue porte `type: s3`, un `endpoints.s3` sur Floci, `use_path_style` et `use_lockfile` a vrai |
| 5 | Le verrou est **effectif** : un `.tflock` depose a la main fait echouer une operation |
| 6 | Le state du consumer porte **une** entree en `mode: data`, servie par le fournisseur integre, et **aucune** ressource geree |
| 7 | Les outputs du consumer valent ceux du producer, et **suivent** quand l'amont change |
| 8 | Le `defaults` rend la valeur de repli pour l'output que le producer ne publie pas |
| 9 | Les deux configurations sont **idempotentes** |

## L'ordre des operations

Le backend doit exister avant d'etre utilise, et le producer avant d'etre lu :

```bash
cd bootstrap && terraform init && terraform apply
cd ../producer && terraform init -backend-config=floci.s3.tfbackend && terraform apply
cd ../consumer && terraform init && terraform apply
```

## Comment verifier, sans rien supposer

La configuration de backend reellement retenue est ecrite par Terraform :

```bash
jq '{type: .backend.type, config: .backend.config}' .terraform/terraform.tfstate
```

Et l'objet dans le bucket se liste avec l'AWS CLI pointee sur l'emulateur :

```bash
aws --endpoint-url http://localhost:14566 s3api list-objects-v2 --bucket tf-state-lab
```

## Le verrou, en deux essais

C'est le coeur du sujet. Deposez un `.tflock` a cote du state, puis planifiez :

```bash
terraform plan -lock-timeout=0s
```

Avec `use_lockfile = true`, la commande **echoue** sur
`Error acquiring the state lock`. Sans l'argument, le **meme** objet est
totalement **ignore** et le plan passe. C'est exactement ce que la validation
verifie.
