# Un tag nomme une version, il ne la fige pas

Versionner un module partagé, c'est découpler le **rythme du module** du
**rythme des projets** qui le consomment. Le mécanisme est simple : un commit, un
tag, une référence côté appelant. Ce qu'on enseigne rarement, c'est ce que ce
mécanisme **ne garantit pas** : un tag Git se déplace, et rien, côté Terraform,
ne mémorise la révision réellement installée.

## Le geste : commit, tag, référence

Côté bibliothèque, une version publiée est un **commit** marqué par un tag
**annoté** :

```bash
git tag -a v1.0.0 -m "1.0.0 : module etiquette initial"
```

Côté consommateur, la référence se pose dans l'URL de la source, après `?ref=` :

```hcl
module "etiquette" {
  source = "git::https://exemple.fr/infra/modules.git//etiquette?ref=v1.0.0"

  prefixe = "atelier"
}
```

Trois morceaux dans cette adresse : le **dépôt**, le **sous-répertoire** derrière
`//`, et la **révision** derrière `?ref=`. L'ordre n'est pas libre, le
sous-répertoire vient avant les arguments de requête.

## Ce que `ref` accepte, et ce qui se passe sans lui

`ref` prend « any value supported by the `git checkout` command », donc un
**tag**, une **branche** ou un **SHA-1**. Son absence n'est pas neutre :

```text
Downloading git::file:///.../depot-modules for plaque...
```

Sans `ref`, Terraform clone la **branche par défaut**. Mesuré sur une
bibliothèque locale : après un nouveau commit sur `main`, un `terraform init
-upgrade` chez le consommateur ramène le nouveau code sans qu'aucune version
n'ait été publiée. C'est le pire réglage possible pour un module partagé, et
c'est le **défaut**.

## Le fait qui change tout : un tag se déplace

Le tag `v1.0.0` désigne un commit, et cette association n'est pas gravée. Un
`git tag -f` la change :

```bash
git tag -f v1.0.0 -m "meme version, autre code"
```

Côté consommateur, rien n'a bougé dans la configuration. Un `terraform init`
seul ne change rien non plus, la copie installée étant conservée. Mais un
`terraform init -upgrade` ramène **un autre code sous le même numéro** :

```text
Upgrading modules...
Downloading git::file:///.../depot-modules?ref=v1.0.0 for plaque...
```

```text
contenu : value = "plaque ${var.etiquette} revision 2"
```

Le même `?ref=v1.0.0`, deux codes différents, sans un message d'avertissement.

## La seule référence immuable : le SHA-1

Reprenons la même expérience, cette fois avec le SHA-1 du commit :

```hcl
source = "git::https://exemple.fr/infra/modules.git//etiquette?ref=72a7572e7a9ede8d490c7611e0455491655301fd"
```

Après le déplacement du tag et un `init -upgrade`, le contenu installé est
**inchangé**. Un SHA-1 désigne un contenu, pas un nom : c'est la seule référence
qu'on ne peut pas redéfinir.

La règle pratique qui en découle : le **tag** pour les environnements qui suivent
les versions publiées, le **SHA-1** pour ce qui doit être reproductible à
l'identique, une base d'audit ou un socle de production figé.

## Ce qui fige vraiment vos modules

Un réflexe hérité des providers trompe beaucoup de monde : le fichier
`.terraform.lock.hcl` ne verrouille **que** les providers. Aucune sélection de
version de module n'y est enregistrée, et un projet sans provider n'en produit
même pas. La révision réellement installée ne tient donc qu'à ce que vous écrivez
dans `source`.

## L'argument `version` n'existe pas ici

Recopier un bloc de registre en changeant seulement la source est l'erreur la
plus fréquente du sujet :

```hcl
module "etiquette" {
  source  = "git::https://exemple.fr/infra/modules.git//etiquette?ref=v1.1.0"
  version = "1.1.0"
}
```

```text
Error: Invalid registry module source address

Failed to parse module registry address: a module registry source address
must have either three or four slash-separated components.

Terraform assumed that you intended a module registry source address because
you also set the argument "version", which applies only to registry modules.
```

Le message explique le raisonnement de Terraform : voyant `version`, il a supposé
une adresse de **registre**, et l'a analysée comme telle.

## SemVer : le numéro dit la nature du changement

| Composant | Quand l'incrémenter | Exemple |
| --- | --- | --- |
| **MAJOR** | changement incompatible | `1.1.0` → `2.0.0` |
| **MINOR** | ajout rétrocompatible | `1.0.1` → `1.1.0` |
| **PATCH** | correction rétrocompatible | `1.0.0` → `1.0.1` |

Le critère est mécanique : tout changement qui **oblige l'appelant à modifier son
bloc `module`** est majeur. Renommer une variable, en supprimer une, en rendre une
obligatoire, renommer une sortie. Ajouter une variable **avec** un `default` est
mineur, précisément parce que l'appelant n'a rien à changer.

## Ce qu'un module réutilisable ne doit pas imposer

La documentation distingue deux rôles. « Reusable modules should constrain only
their **minimum** allowed versions », tandis que « Root modules should use a `~>`
constraint to set both a lower and upper bound ». La raison se mesure : un module
qui pose une borne haute la propage à tous ses consommateurs.

```text
- Finding hashicorp/local versions matching "~> 2.4.0, >= 2.9.0"...

Error: Failed to query available provider packages

Could not retrieve the list of available versions for provider
hashicorp/local: no available releases match the given constraints ~> 2.4.0,
>= 2.9.0
```

Les contraintes du module et de la racine s'**intersectent**. Le module a bloqué
un projet qui, lui, avait besoin d'une version plus récente.

## Accélérer un clone : `depth`

Sur un dépôt de modules à l'historique long, `depth=1` réduit nettement le temps
d'`init` :

```hcl
source = "git::https://exemple.fr/infra/modules.git//etiquette?ref=v1.1.0&depth=1"
```

Attention à la contrepartie, mesurée : avec `depth`, la révision est passée à
`git clone --branch`, ce qui n'accepte **pas** un SHA-1 brut.

```text
fatal: Remote branch 72a7572e7a9ede8d490c7611e0455491655301fd not found
```

Un `depth=1` et un épinglage par SHA-1 sont donc incompatibles.

## À vous de jouer

Vous savez publier une version, choisir entre tag et SHA-1, reconnaître ce qui
rend un changement majeur, et pourquoi `version` n'a pas sa place sur une source
Git. Le challenge vous fait publier trois versions d'un module, puis les
consommer depuis trois projets, chacun avec sa forme de référence.

```bash
dsoxlab run modules-version-modules
dsoxlab check modules-version-modules
dsoxlab hint modules-version-modules
```

Il se joue **hors ligne** : la bibliothèque est un dépôt Git local.

Sous-objectif d'examen visé : **4c** (refactorer et versionner un module).

Référence : [versionner ses modules](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/modules/versionner-modules/)
