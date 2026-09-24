# 🎯 Challenge : contraindre la CLI, verrouiller les providers

## Point de départ

`challenge/work` ne contient qu'un `main.tf` **vide**. Aucun `.terraform/`,
aucun `.terraform.lock.hcl`, aucun provider téléchargé.

Aucune VM, aucun cloud : le réseau n'est nécessaire que pour télécharger les
providers.

## ✅ Objectif

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

## 🧭 Trois choses que l'on confond

**`required_version` ne porte pas sur les providers.** Il ne contraint que la
CLI. Épingler Terraform n'épingle rien de ce qu'il télécharge : c'est
`required_providers` qui s'en charge, et le verrou qui le fige.

**Ce n'est pas la même chose qu'un `.terraform-version`.** Celui-ci dit quelle
CLI **installer** sur votre poste. `required_version` dit quelle CLI a le droit
d'**exécuter** cette configuration, et il voyage avec elle dans le dépôt.

**Un verrou est fait pour être commité.** Ce n'est pas un cache. C'est lui qui
garantit que le collègue obtient les mêmes versions que vous, et il ne le peut
que s'il est dans le dépôt.

## ⚠️ Le piège qui ne se voit qu'ailleurs

Les sommes de contrôle du verrou sont **par plateforme**. Un verrou créé sur
Linux ne contient pas celles de macOS : l'`init` du collègue échouera sur un
fichier que vous avez pourtant commité, et le message parlera de somme
manquante, jamais de plateforme.

```bash
terraform providers lock -platform=linux_amd64 -platform=darwin_arm64
```

À relancer **chaque fois qu'une contrainte change**.

## 🔍 Validation

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
