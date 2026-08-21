# Le verrou S3 ne s'active pas tout seul

Deux croyances font tomber les candidats sur cet objectif. Que déclarer un
`backend "s3"` suffit à **verrouiller** le state. Et qu'un bloc `backend` se
paramètre par des variables, comme le reste du HCL. Les deux sont fausses, et se
mesurent.

## Un bloc `backend` refuse toute valeur nommée

```hcl
terraform {
  backend "s3" {
    bucket = var.backend_bucket
  }
}
```

```text
Error: Variables not allowed

  on main.tf line 8, in terraform:
   8:     bucket = var.backend_bucket

Variables may not be used here.
```

L'`init` sort en **1**. Le backend est lu **avant** l'évaluation des variables :
il ne peut rien en connaître. C'est la raison d'être de la **configuration
partielle**, et non une simple commodité.

## La configuration partielle, en fichier

Le bloc reste **vide**, et les arguments arrivent à l'initialisation :

```bash
terraform init -backend-config=floci.s3.tfbackend
```

La forme **fichier** vaut mieux que `-backend-config="cle=valeur"`, que la
documentation déconseille pour un secret : l'historique du shell le conserve. Le
nommage recommandé est `*.<backend>.tfbackend`.

## Vérifier ce que Terraform a retenu

Ces valeurs ne figurent alors dans **aucun** fichier `.tf`. Terraform les écrit
pourtant, et c'est la seule preuve fiable :

```bash
jq '{type: .backend.type, config: .backend.config}' .terraform/terraform.tfstate
```

```text
{
  "type": "s3",
  "config": {
    "bucket": "tf-state-lab",
    "key": "producer/terraform.tfstate",
    "use_path_style": true,
    "use_lockfile": true,
    "endpoints": { "s3": "http://localhost:14566" }
  }
}
```

Attention, ce fichier **n'est pas un coffre** : la configuration y figure
entièrement **résolue**, identifiants compris. La configuration partielle protège
le **dépôt**, pas le **disque**.

## Le verrouillage est un opt-in strict

C'est le cœur du lab. `use_lockfile` vaut **`false`** par défaut. Déposez un
`.tflock` à côté du state, puis planifiez.

Avec `use_lockfile = true` :

```text
Error: Error acquiring the state lock

Error message: operation error S3: PutObject, https response error
```

Code **1**. Sans l'argument, et avec le **même** objet toujours présent, le plan
passe en code **0** : le verrou est purement **ignoré**, et deux applies
concurrents s'écrasent en silence.

Le verrouillage natif S3 date de Terraform **1.10**. Le verrou par table
**DynamoDB** est déprécié.

## Après migration, il ne reste rien en local

Beaucoup de tutoriels font suivre la migration d'un `rm -rf terraform.tfstate`.
Mesuré, il n'y a **rien** à supprimer :

```text
state local du producer : AUCUN
objets dans le bucket : ['producer/terraform.tfstate']
```

## `defaults` comble un trou, pas une absence

L'argument fournit une valeur de repli « in case the state file is empty or lacks
a required output ». La nuance compte :

- l'état **existe** mais l'output **manque** : le repli **joue** ;
- la clé de state **n'existe pas** : Terraform rend
  `Error: Unable to find remote state`, code **1**.

`defaults` ne remplace donc pas un `apply` de la stack amont.

## À vous de jouer

```bash
dsoxlab run aws-backend-s3-remote-state
dsoxlab check aws-backend-s3-remote-state
dsoxlab hint aws-backend-s3-remote-state
```

L'émulateur S3 est déclaré en `runtime.services` : **dsoxlab le démarre tout
seul**, sur `http://localhost:14566`. Aucun compte AWS n'est nécessaire.

Sous-objectif d'examen visé : **3b**, avec **3d** en appui.

Référence : [backend S3 et terraform_remote_state](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/backend-s3-remote-state/)
