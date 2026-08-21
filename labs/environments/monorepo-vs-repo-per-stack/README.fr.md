# Séparer les stacks sépare les états

Le choix monorepo ou dépôt par stack se discute en termes d'organisation. Sa
**conséquence technique**, elle, ne se discute pas : découper en stacks découpe
les **états**, et une stack ne voit plus rien de l'autre tant qu'on n'a pas
**publié** explicitement ce qu'elle doit partager.

## Un module local n'accepte pas `version`

Ce n'est pas une commodité qu'on choisit, c'est un **refus**. Mesuré :

```hcl
module "reseau" {
  source  = "./modules/reseau"
  version = "~> 1.0"
}
```

```text
Error: Invalid registry module source address

Failed to parse module registry address: can't use local directory
"./modules/reseau" as a module registry address.

Terraform assumed that you intended a module registry source address because
you also set the argument "version", which applies only to registry modules.
```

L'`init` sort en **1**. La documentation l'explique : « Modules sourced from
local file paths do not support `version` because they're loaded from the same
source repository and always share the same version as their caller. »

Corollaire souvent ignoré : **seule** la forme registre
(`source = "<NAMESPACE>/<NAME>/<PROVIDER>"`) accepte une **contrainte** comme
`~> 1.3`. Avec `git::...?ref=v1.3.0`, le versionnement est un **pinning
littéral**, pas une contrainte que Terraform résout.

## Seules les sorties de la RACINE traversent

C'est le piège numéro un quand on éclate un monorepo. Une sortie déclarée dans un
module **imbriqué** n'est pas visible depuis une autre configuration. Mesuré, sur
une stack amont qui appelle un module et ne ré-exporte qu'une valeur :

```text
Error: Unsupported attribute

data.terraform_remote_state.amont.outputs is object with 1 attribute "reexporte"
This object does not have an attribute named "identifiant_interne".
```

Ce qui doit franchir la frontière se **ré-exporte** donc à la racine :

```hcl
output "network_cidr" {
  value = module.reseau.network_cidr
}
```

## Publier une sortie, c'est publier tout l'état

L'avertissement de la documentation mérite d'être cité en entier :

> any user or server which has enough access to read the root module output
> values will also always have access to the full state snapshot data by direct
> network requests.

Autrement dit, donner accès aux **sorties** d'une stack, c'est donner accès au
**snapshot complet** de son état. Un mot de passe n'a donc rien à faire dans une
sortie racine, **même** marqué `sensitive` : cet argument masque l'affichage, pas
l'état.

Mesuré, `terraform output -json` restitue d'ailleurs une valeur `sensitive`
**en clair** ; seul l'affichage texte la masque.

La documentation recommande à la place une publication **explicite** vers un
magasin dédié, plutôt qu'un partage d'état.

## Deux arguments utiles de `terraform_remote_state`

**`defaults`** comble un output **manquant** dans un état qui **existe** :

```hcl
data "terraform_remote_state" "amont" {
  backend = "local"

  config = {
    path = "../amont/terraform.tfstate"
  }

  defaults = {
    identifiant = "valeur-de-repli"
  }
}
```

Mesuré : la valeur de repli est bien retenue quand l'output est absent. En
revanche, si l'état amont **n'existe pas du tout**, `defaults` ne sauve rien :

```text
Error: Unable to find remote state

No stored state was found for the given workspace in the given backend.
```

**`workspace`** désigne le workspace de la stack amont à lire. Attention, sur un
backend `local` dont le `path` pointe un **fichier** précis, la mesure rend la
même erreur `Unable to find remote state` : cet argument prend son sens sur un
backend qui adresse nativement ses workspaces.

## À vous de jouer

```bash
dsoxlab run environments-monorepo-vs-repo-per-stack
dsoxlab check environments-monorepo-vs-repo-per-stack
dsoxlab hint environments-monorepo-vs-repo-per-stack
```

Il se joue **hors ligne**, avec les providers `local` et `random`.

Sous-objectif d'examen visé : **3d**, avec **3b** en appui.

Référence : [monorepo vs repo par stack](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/environnements/monorepo-vs-repo-par-stack/)
