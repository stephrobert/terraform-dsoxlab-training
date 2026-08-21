# Les backends Terraform : où vit le state, et comment le configurer

Un **backend** décide **où** Terraform stocke le state et **comment** il le
verrouille. Par défaut, c'est le backend **`local`** : un `terraform.tfstate` dans
le dossier courant. En équipe, on le déplace vers un backend **distant** (S3, GCS,
HCP…) pour partager le state et le verrouiller. Ce tutoriel montre la mécanique de
configuration, ses pièges, et la migration ; le challenge vous la fera prouver sur
un backend `local` paramétré.

## Le piège : le bloc backend n'accepte aucune valeur nommée

Le bloc `backend` est lu **très tôt**, avant l'évaluation des variables. Il
**n'accepte donc aucune valeur nommée** : ni `var.`, ni `local.`, ni attribut de
data source. Ceci échoue :

```hcl
terraform {
  backend "local" {
    path = var.chemin_state   # Error: Variables not allowed
  }
}
```

C'est exactement la raison d'être de la **configuration partielle**.

## La configuration partielle et `-backend-config`

On laisse le bloc backend **incomplet**, et on fournit le reste à l'`init` :

```hcl
terraform {
  backend "local" {}   # partiel : aucun path ici
}
```

```bash
terraform init -backend-config=dev.local.tfbackend
```

Le fichier `dev.local.tfbackend` porte `path = "etat/dev/terraform.tfstate"`. Un
**fichier par environnement** (`dev`, `prod`…) alimente le **même** bloc backend
sans jamais coder le chemin en dur. Réinitialisé **sans** `-backend-config`, un
bloc partiel résout ses valeurs à `null` : c'est la preuve qu'il est bien partiel.

Terraform enregistre la configuration **résolue** dans
`.terraform/terraform.tfstate` (`backend.type` et `backend.config`), un fichier
local qui n'est pas le state lui-même.

## Migrer un state existant : `-migrate-state`

Quand on ajoute ou change un backend sur un projet **déjà appliqué**, Terraform
propose de **migrer** le state, sans le recréer :

```bash
terraform init -migrate-state -backend-config=dev.local.tfbackend
```

Le state garde son **`lineage`** : c'est la preuve d'une migration, pas d'un apply
neuf (qui, lui, fabriquerait un lineage différent). À distinguer de
**`-reconfigure`**, qui **ignore** le state existant et repart de zéro sur le
nouveau backend, sans migration. Choisir l'un ou l'autre par erreur est une source
classique de state perdu.

## À vous de jouer

Vous savez que le bloc backend refuse les valeurs nommées, que la configuration
partielle plus `-backend-config` donne un fichier par environnement, qu'un bloc
partiel résout à `null` sans config, et que `-migrate-state` déplace un state en
conservant son `lineage`. Le challenge vous fait passer un projet du backend local
implicite à un backend `local` paramétré, en migrant le state.

```bash
dsoxlab run state-backends
dsoxlab check state-backends
dsoxlab hint state-backends
```

Sous-objectif d'examen visé : **3b** (remote state), niveau Professional.

Référence : [Les backends Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/backends-terraform/)
