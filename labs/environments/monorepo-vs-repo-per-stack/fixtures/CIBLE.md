# Decouper un monorepo en deux stacks qui se parlent

Separer les stacks separe les **etats**. Une stack ne voit alors plus rien de
l'autre tant qu'on n'a pas **publie** explicitement ce qu'elle doit partager.

## Ce que contient le depot

| Chemin | Ce que c'est |
| --- | --- |
| `modules/reseau/` | module local **complet**, a ne pas modifier |
| `stacks/plateforme/` | appelle le module, `outputs.tf` **vide**, un secret declare |
| `stacks/applicatif/` | consomme la plateforme, bloc `data` **troue** |

Rien n'est initialise, aucun etat n'existe.

## L'etat a atteindre

| Point | Attendu |
| --- | --- |
| 1 | `stacks/plateforme` s'initialise |
| 2 | Son etat contient les ressources du module, dont `random_password.db` |
| 3 | Ses sorties racine exposent `network_name` et `network_cidr` |
| 4 | **Aucune** sortie racine ne porte le mot de passe |
| 5 | `stacks/applicatif` a une entree `mode: data` de type `terraform_remote_state` |
| 6 | Son `network_cidr` vaut **exactement** celui de la plateforme, et son fichier le contient |
| 7 | Les deux stacks sont **idempotentes** |

## Trois faits qui decident du travail

**Un module local n'accepte pas `version`.** Ce n'est pas une commodite, c'est
un refus :

```text
Error: Invalid registry module source address

Terraform assumed that you intended a module registry source address because
you also set the argument "version", which applies only to registry modules.
```

**Seules les sorties de la RACINE traversent.** Une sortie de module imbrique
reste invisible depuis une autre configuration :

```text
Error: Unsupported attribute

data.terraform_remote_state.amont.outputs is object with 1 attribute "reexporte"
```

Ce qui doit traverser se **re-exporte** donc a la racine, explicitement.

**Publier une sortie, c'est publier tout l'etat.** La documentation est
formelle : « any user or server which has enough access to read the root module
output values will also always have access to the full state snapshot data by
direct network requests. » Un mot de passe n'a donc rien a faire dans une sortie
racine, meme marque `sensitive`.

## Comment verifier

Le CIDR est **tire au sort** a l'apply : le recopier a la main ne tiendra pas.

```bash
cd stacks/plateforme && terraform output -json
cd ../applicatif && terraform output -json

terraform show -json | jq '.values.root_module.resources[] | {address, mode}'
```
