# Examen blanc Terraform Associate 004

Quarante questions, etiquetees par sous-objectif officiel. Repondez dans
`reponses.auto.tfvars`, une entree par question.

| Type | Ce qu'on attend |
| --- | --- |
| choix unique | **une** lettre, par exemple `b` |
| vrai / faux | `v` ou `f` |
| choix multiple | les lettres **triees**, collees, par exemple `ac` |
| atelier | la valeur relevee dans `atelier/`, en minuscules |

Les quatre dernieres questions n'ont de reponse **qu'apres** avoir construit
et applique `atelier/`. Elles portent sur l'etat qu'il produit.

La casse et les espaces autour de la reponse sont ignores.

---

## q01 — objectif 1a — choix unique

Qu'est-ce qui distingue le plus surement de l'infrastructure as code d'un script de provisionnement ?

- **a.** le langage utilise est declaratif plutot qu'imperatif
- **b.** l'outil maintient un etat qui lui permet de converger vers la cible decrite
- **c.** le code est stocke dans un depot Git
- **d.** l'execution est idempotente

## q02 — objectif 1b — choix multiple

Parmi ces avantages, lesquels sont directement apportes par une pratique IaC ? (plusieurs reponses)

- **a.** la revue par les pairs des changements d'infrastructure
- **b.** la suppression totale des pannes en production
- **c.** la reproductibilite d'un environnement a l'identique
- **d.** la garantie que le fournisseur ne changera pas son API

## q03 — objectif 2a — choix unique

Quel fichier fige les versions de providers reellement installees, avec leurs sommes de controle ?

- **a.** .terraform/providers.json
- **b.** .terraform.lock.hcl
- **c.** versions.tf
- **d.** terraform.tfstate

## q04 — objectif 2a — choix unique

Les sommes de controle du fichier de verrouillage sont enregistrees :

- **a.** une seule fois, valables pour toutes les plateformes
- **b.** par plateforme, ce qui impose `terraform providers lock -platform=...` pour une equipe heterogene
- **c.** par version de Terraform
- **d.** uniquement pour les providers officiels HashiCorp

## q05 — objectif 2b — vrai / faux

`required_version` dans le bloc `terraform` contraint aussi les versions des providers.

## q06 — objectif 2d — choix unique

A quoi sert le state de Terraform ?

- **a.** a stocker les identifiants d'acces au fournisseur
- **b.** a associer chaque objet reel a l'adresse qui le declare, et a memoriser ses attributs
- **c.** a conserver l'historique de tous les apply
- **d.** a remplacer le fichier de verrouillage

## q07 — objectif 3b — choix unique

Que fait `terraform init` en plus de telecharger les providers ?

- **a.** il applique la configuration
- **b.** il parse la configuration, et echoue donc sur une erreur de syntaxe
- **c.** il verifie que les ressources existent chez le fournisseur
- **d.** il supprime le state local

## q08 — objectif 3c — vrai / faux

`terraform validate` peut s'executer utilement avant `terraform init`.

## q09 — objectif 3c — choix unique

`terraform validate` detecte lequel de ces defauts ?

- **a.** une valeur d'argument refusee par l'API du fournisseur
- **b.** un attribut qui n'existe dans le schema d'aucun provider
- **c.** une ressource supprimee a la main chez le fournisseur
- **d.** un conflit de verrou sur le state distant

## q10 — objectif 3d — choix unique

`terraform plan -detailed-exitcode` rend 2. Cela signifie :

- **a.** la commande a echoue
- **b.** il n'y a aucun changement
- **c.** le plan a reussi et contient des changements
- **d.** le state est verrouille

## q11 — objectif 3e — choix unique

Appliquer un plan enregistre par `-out` garantit :

- **a.** que l'apply n'attend aucune confirmation et applique exactement ce plan
- **b.** que l'apply relira la configuration au moment d'appliquer
- **c.** que le state ne sera pas modifie
- **d.** que les data sources ne seront pas relues

## q12 — objectif 3f — vrai / faux

`terraform destroy` supprime le fichier `terraform.tfstate`.

## q13 — objectif 3g — choix unique

`terraform fmt -check` sur un fichier hors format canonique rend le code :

- **a.** 1
- **b.** 2
- **c.** 3
- **d.** 0 avec un avertissement

## q14 — objectif 4a — choix unique

Quelle difference fondamentale separe un bloc `data` d'un bloc `resource` ?

- **a.** le bloc `data` ne peut pas etre utilise avec `for_each`
- **b.** le bloc `data` lit sans creer, et n'apparait dans aucun plan de destruction
- **c.** le bloc `data` n'apparait jamais dans le state
- **d.** le bloc `data` ne peut pas dependre d'une ressource

## q15 — objectif 4b — vrai / faux

Referencer l'attribut d'une ressource cree une dependance implicite, et attend que cette ressource ait fini d'etre appliquee.

## q16 — objectif 4c — choix unique

Parmi ces sources de valeur, laquelle l'emporte sur toutes les autres ?

- **a.** la variable d'environnement TF_VAR_
- **b.** le fichier terraform.tfvars
- **c.** un fichier *.auto.tfvars
- **d.** l'option -var en ligne de commande

## q17 — objectif 4c — choix unique

Une variable est posee a la fois par TF_VAR_ et par terraform.tfvars. Laquelle gagne ?

- **a.** TF_VAR_, car une variable d'environnement ecrase un fichier
- **b.** terraform.tfvars, car les fichiers de valeurs sont charges apres
- **c.** cela depend de l'ordre alphabetique
- **d.** Terraform refuse de planifier et demande de trancher

## q18 — objectif 4d — choix unique

`for_each` accepte :

- **a.** une liste ou un set
- **b.** une map ou un set de chaines
- **c.** n'importe quelle collection
- **d.** un nombre

## q19 — objectif 4d — vrai / faux

Sur une ressource pilotee par `for_each`, la syntaxe splat `[*]` leve une erreur.

## q20 — objectif 4e — choix unique

`element(["dev","staging","prod"], 5)` rend :

- **a.** une erreur d'index hors bornes
- **b.** "dev"
- **c.** "prod"
- **d.** null

## q21 — objectif 4e — choix unique

`lookup({dev = "small"}, "qa")`, sans troisieme argument, rend :

- **a.** null
- **b.** une chaine vide
- **c.** une erreur
- **d.** "small"

## q22 — objectif 4f — choix unique

Quand `depends_on` est-il justifie ?

- **a.** chaque fois qu'un ordre precis est souhaite
- **b.** quand la ressource n'utilise aucune donnee de l'amont et en depend pourtant
- **c.** quand la ressource reference deja un attribut de l'amont
- **d.** pour forcer la relecture d'une data source

## q23 — objectif 4g — choix multiple

Parmi ces mecanismes, lesquels ARRETENT Terraform quand leur condition est fausse ? (plusieurs reponses)

- **a.** le bloc `validation` d'une variable
- **b.** la `precondition` d'un bloc `lifecycle`
- **c.** le bloc `check` au niveau racine
- **d.** la `postcondition` d'un bloc `lifecycle`

## q24 — objectif 4h — choix unique

Quelle affirmation decrit correctement `sensitive = true` sur un output ?

- **a.** la valeur est chiffree dans le state
- **b.** la valeur est masquee a l'affichage et reste en clair dans le state
- **c.** la valeur est supprimee du state
- **d.** la valeur n'est lisible que par le proprietaire du workspace

## q25 — objectif 5a — choix unique

Quelle source de module NE telecharge PAS depuis le reseau ?

- **a.** un chemin local commencant par ./ ou ../
- **b.** le Terraform Registry
- **c.** un depot Git
- **d.** un bucket S3

## q26 — objectif 5b — vrai / faux

Un module enfant herite automatiquement des variables declarees dans le module racine.

## q27 — objectif 5c — choix unique

Un module destine a etre appele plusieurs fois :

- **a.** doit declarer ses propres blocs `provider`
- **b.** ne doit contenir aucun bloc `provider`, les configurations lui etant passees par l'appelant
- **c.** doit obligatoirement porter un `count`
- **d.** ne peut pas declarer de `required_providers`

## q28 — objectif 5d — choix unique

L'argument `version` d'un bloc `module` est utilisable :

- **a.** pour toutes les sources de module
- **b.** uniquement pour les modules provenant d'un registry
- **c.** uniquement pour les modules locaux
- **d.** uniquement avec HCP Terraform

## q29 — objectif 6a — vrai / faux

Sans bloc `backend`, Terraform ecrit terraform.tfstate dans le repertoire de travail.

## q30 — objectif 6b — choix unique

A quoi sert le verrouillage du state ?

- **a.** a chiffrer le state au repos
- **b.** a empecher deux operations concurrentes d'ecrire le state en meme temps
- **c.** a empecher la destruction des ressources
- **d.** a verrouiller les versions de providers

## q31 — objectif 6c — vrai / faux

Un bloc `backend` peut referencer une variable d'entree pour son chemin ou son bucket.

## q32 — objectif 6d — choix unique

Quelle commande aligne le state sur la realite SANS modifier l'infrastructure ?

- **a.** terraform apply -refresh-only
- **b.** terraform apply -auto-approve
- **c.** terraform state rm
- **d.** terraform force-unlock

## q33 — objectif 6d — choix unique

Un bloc `removed` portant `lifecycle { destroy = false }` :

- **a.** detruit l'objet et le retire du state
- **b.** retire la ressource du state en laissant l'objet en place
- **c.** empeche toute destruction future
- **d.** renomme la ressource dans le state

## q34 — objectif 7a — vrai / faux

Un import est termine des que la ressource apparait dans `terraform state list`.

## q35 — objectif 7c — choix unique

Pour isoler une trace de debogage dans un fichier plutot que sur le terminal :

- **a.** TF_LOG=DEBUG seul suffit
- **b.** TF_LOG=DEBUG avec TF_LOG_PATH
- **c.** terraform plan -debug
- **d.** terraform plan > trace.log

## q36 — objectif 8c — choix unique

Dans HCP Terraform, un projet sert a :

- **a.** stocker les versions de providers
- **b.** regrouper des workspaces et porter des permissions communes
- **c.** remplacer le fichier de verrouillage
- **d.** executer les plans localement

## q37 — objectif 7b — atelier

Dans `atelier`, combien d'objets le state porte-t-il en `mode: managed` ? (un nombre, releve par `terraform show -json`)

## q38 — objectif 7b — atelier

Dans `atelier`, quelle est l'adresse complete du seul bloc en `mode: data` ? (par exemple `data.type.nom`)

## q39 — objectif 7b — atelier

Dans `atelier`, quel code rend `terraform plan -detailed-exitcode` juste apres l'apply ? (un chiffre)

## q40 — objectif 4h — atelier

Dans `atelier`, la valeur de l'output marque `sensitive` apparait-elle en clair dans `terraform.tfstate` ? (v ou f)
