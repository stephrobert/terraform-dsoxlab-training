# Contraindre la version de Terraform et verrouiller les providers

## La situation

**Sous-objectif d'examen visé : 3a, gérer l'installation et le versionnement de Terraform et des providers.**

Installer un binaire ne prouve presque rien. Ce qui compte, c'est de savoir imposer une version de CLI à une configuration et figer les providers qu'elle télécharge, pour que la même configuration se comporte de la même façon sur tous les postes de l'équipe.

## Capacité visée

Déclarer une contrainte `required_version` dans le bloc `terraform {}`, la faire échouer volontairement pour observer le refus d'exécution, épingler les providers via `required_providers`, puis exploiter le fichier de verrouillage `.terraform.lock.hcl` que `terraform init` produit.

La doc officielle est explicite sur la frontière : `required_version` ne porte que sur la version de la CLI, jamais sur celle des providers. Ce sont deux mécanismes distincts, et le lab oblige à manipuler les deux.

## D'où part l'apprenant

Terraform est installé par l'une des méthodes du guide et `terraform version` répond. L'apprenant sait épingler une version au niveau de l'outillage (`mise.toml`, `.terraform-version`), mais il ignore que la configuration elle-même porte sa propre contrainte, et il n'a jamais ouvert un fichier de verrouillage.

Le répertoire de travail `challenge/work` ne contient qu'un `main.tf` vide. Aucun `.terraform/`, aucun `.terraform.lock.hcl`, aucun provider téléchargé. Le lab est de type `shell` : il ne consomme aucune machine virtuelle et n'exige aucun accès à un cloud.

## L'état à atteindre

Dans `challenge/work` :

1. Un bloc `terraform {}` porte un `required_version` satisfait par la CLI installée, et un `required_providers` déclarant `hashicorp/local`, `hashicorp/null` et `hashicorp/random` avec des contraintes de version explicites.
2. La configuration crée une ressource de chacun de ces trois providers, sans autre accès réseau que le téléchargement des providers.
3. `terraform init` a réussi et a produit `.terraform.lock.hcl`, contenant les trois providers avec leurs sommes de contrôle.
4. `terraform providers lock` a été relancé pour au moins deux plateformes, afin que le verrou couvre des postes hétérogènes.
5. La configuration a été appliquée : l'état est convergé.

Dans un sous-répertoire `echec-version/` :

6. Une configuration minimale dont le `required_version` ne peut pas être satisfait par la CLI installée, qui sert de contre-exemple.

## Comment on le prouve

La validation n'ouvre jamais les fichiers `.tf` écrits par l'apprenant et ne parse aucune sortie destinée à un humain. Elle s'appuie uniquement sur des sorties structurées et des codes retour :

- `terraform version -json` dans `challenge/work` : la version rapportée satisfait la contrainte, et `provider_selections` liste exactement les trois providers attendus.
- `terraform init` lancé dans `echec-version/` renvoie un code retour non nul, alors que le même appel dans `challenge/work` renvoie 0. C'est le refus d'exécution sur contrainte non satisfaite qui est prouvé, pas la présence d'un texte.
- `.terraform.lock.hcl` est analysé comme le fichier machine qu'il est : trois blocs `provider`, chacun avec sa version résolue, ses `constraints` et au moins une somme `h1:`, pour deux plateformes au minimum.
- Le répertoire `.terraform/` est supprimé, puis `terraform init` est relancé : `provider_selections` doit rester strictement identique. C'est la preuve que le verrou fait autorité et que rien n'a glissé vers une version plus récente.
- `terraform plan -detailed-exitcode` renvoie 0, ce qui prouve que l'état est appliqué et convergé. Un code 2 signalerait une configuration jamais appliquée.

Ces cinq preuves échouent toutes si l'apprenant s'est contenté d'installer le binaire.

## 🎯 Challenge : contraindre la CLI, verrouiller les providers

### Point de départ

`challenge/work` ne contient qu'un `main.tf` **vide**. Aucun `.terraform/`,
aucun `.terraform.lock.hcl`, aucun provider téléchargé.

Aucune VM, aucun cloud : le réseau n'est nécessaire que pour télécharger les
providers.

### ✅ Objectif

Dans `challenge/work` :

1. **Un bloc `terraform {}`** portant un `required_version` que votre CLI
   satisfait, et un `required_providers` déclarant `hashicorp/local`,
   `hashicorp/null` et `hashicorp/random` avec des contraintes **explicites**.
2. **Une ressource de chacun** de ces trois providers.
3. **`terraform init`** réussi, produisant `.terraform.lock.hcl` avec les trois
   providers et leurs sommes de contrôle.
4. **`terraform providers lock`** relancé pour **au moins deux plateformes**.
5. **La configuration appliquée**, état convergé.

Dans un sous-répertoire `echec-version/` :

6. **Une configuration minimale** dont le `required_version` ne peut **pas**
   être satisfait par votre CLI.

### 🧭 Trois choses que l'on confond

**`required_version` ne porte pas sur les providers.** Il ne contraint que la
CLI. Épingler Terraform n'épingle rien de ce qu'il télécharge : c'est
`required_providers` qui s'en charge, et le verrou qui le fige.

**Ce n'est pas la même chose qu'un `.terraform-version`.** Celui-ci dit quelle
CLI **installer** sur votre poste. `required_version` dit quelle CLI a le droit
d'**exécuter** cette configuration, et il voyage avec elle dans le dépôt.

**Un verrou est fait pour être commité.** Ce n'est pas un cache. C'est lui qui
garantit que le collègue obtient les mêmes versions que vous, et il ne le peut
que s'il est dans le dépôt.

### ⚠️ Le piège qui ne se voit qu'ailleurs

Les sommes de contrôle du verrou sont **par plateforme**. Un verrou créé sur
Linux ne contient pas celles de macOS : l'`init` du collègue échouera sur un
fichier que vous avez pourtant commité, et le message parlera de somme
manquante, jamais de plateforme.

```bash
terraform providers lock -platform=linux_amd64 -platform=darwin_arm64
```

À relancer **chaque fois qu'une contrainte change**.

### 🔍 Validation

```bash
dsoxlab check getting-started-install-terraform
```

Aucun test n'ouvre vos `.tf`. La preuve centrale est celle du verrou : le
répertoire `.terraform/` est supprimé, `init` est relancé, et
`provider_selections` doit rester **strictement identique**. Si les versions
bougeaient, le verrou ne servirait à rien.

Le sous-répertoire d'échec est jugé sur son **code retour**, pas sur son
message : un texte change avec les versions.

Bloqué ? `dsoxlab hint getting-started-install-terraform`.
