# Le critère n'est pas l'environnement, c'est le backend

La question « workspaces ou configurations séparées ? » se tranche par une seule
propriété, et elle est **technique**, pas organisationnelle.

## La raison qui explique tout le reste

Un bloc `backend` **ne peut référencer aucune valeur nommée**. Mesuré :

```hcl
terraform {
  backend "local" {
    path = "etats/${terraform.workspace}.tfstate"
  }
}
```

```text
Error: Variables not allowed

  on main.tf line 3, in terraform:
   3:     path = "etats/${terraform.workspace}.tfstate"

Variables may not be used here.
```

`terraform.workspace` est donc **inutilisable** dans un backend. Tous les
workspaces d'un répertoire écrivent forcément au **même endroit**, avec les
**mêmes** droits d'accès à l'état.

## Le bloc `provider`, lui, accepte les expressions

C'est la dissymétrie que beaucoup de guides ratent, et elle change la conclusion.
Le **même** `terraform.workspace`, dans un bloc `provider` :

```hcl
provider "tls" {
  proxy {
    url = "http://proxy-${terraform.workspace}.exemple.invalide:3128"
  }
}
```

Mesuré : `init` et `plan` passent, en code **0**.

Autrement dit, on **peut** faire varier par workspace le rôle avec lequel on
crée les ressources, comme le montre la documentation du backend S3 avec
`assume_role = { role_arn = var.workspace_iam_roles[terraform.workspace] }`. Ce
qu'on ne peut **pas** faire varier, c'est le **stockage de l'état** et les droits
qui le protègent.

## Ce que les workspaces isolent, et ce qu'ils n'isolent pas

Ils isolent l'**état**. Pas les objets réels. La démonstration tient en trois
commandes :

```bash
terraform workspace new dev && terraform apply -auto-approve   # produit app.conf
terraform workspace new prod
terraform plan
```

```text
  # local_file.app will be created
Plan: 1 to add, 0 to change, 0 to destroy.
```

Le fichier `app.conf` est pourtant **toujours** sur le disque : `prod` ne le voit
pas, parce qu'il n'est pas dans **son** état. Un apply dans `prod` l'**écrase**
sans jamais l'avoir vu. Deux workspaces qui visent le même objet se marchent
donc dessus en silence.

## Le cas où les workspaces restent le bon outil

Une même infrastructure, des **variations légères**, les mêmes droits, le même
backend. Le motif classique est une map indexée par le workspace :

```hcl
locals {
  tailles = {
    default = 1
    dev     = 2
    prod    = 8
  }
}

output "taille" {
  value = lookup(local.tailles, terraform.workspace, local.tailles["default"])
}
```

Mesuré : `dev` rend **2**, `prod` rend **8**. Le troisième argument de `lookup`
est le **repli**, utilisé quand le workspace ne figure pas dans la map.

## Ce que coûte la découpe

Séparer en configurations n'est pas gratuit, et la documentation le dit :
« Terraform installs a separate cache of plugins and modules for each working
directory. » Mesuré sur ce lab, chaque répertoire de travail installe son propre
cache, de l'ordre de **18 Mo** ici. S'y ajoutent la mise à jour et la
réinitialisation de **chaque** répertoire séparément.

## Et la donnée, alors ?

Une fois séparées, deux racines ne se parlent plus toutes seules. La passerelle
officielle est la lecture de l'**état distant** de l'autre, par ses **outputs
déclarés** :

```hcl
data "terraform_remote_state" "socle" {
  backend = "local"

  config = {
    path = "../socle/terraform.tfstate"
  }
}
```

La documentation signale le compromis : cela « creates a tighter coupling between
configurations ».

## À vous de jouer

```bash
dsoxlab run environments-when-to-use-workspaces
dsoxlab check environments-when-to-use-workspaces
dsoxlab hint environments-when-to-use-workspaces
```

Il se joue **hors ligne**, avec les providers `local` et `random`.

Sous-objectif d'examen visé : **3d**.

Référence : [quand utiliser les workspaces](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/quand-utiliser-workspaces/)
