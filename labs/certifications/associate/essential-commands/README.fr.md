# Les commandes essentielles, et ce qu'elles refusent de faire

L'Associate 004 est un **QCM d'une heure**. On n'y tape rien, et c'est
exactement le piège : réviser un tableau de commandes donne l'illusion de
savoir, jusqu'à la question qui porte sur ce qu'une commande **refuse** de
faire, ou sur le code qu'elle rend en échouant.

Ce lab ne révise pas ce tableau. Il fait **relever six codes de retour** sur un
cluster de fichiers qui tient dans un répertoire, et chaque code dément une
formule qu'on récite sans l'avoir vérifiée.

## `validate` n'est pas un correcteur orthographique

La formule qui circule est « `validate` ne vérifie que la syntaxe ». Elle est
fausse des deux côtés.

**D'un côté, il en fait moins qu'on croit** : il a besoin des **schémas** des
providers, donc il ne peut rien valider avant `init`. Lancé sur un répertoire
neuf, il sort en **1**, non pas parce que la configuration est mauvaise, mais
parce qu'il n'a pas de quoi juger.

```console
$ terraform validate
╷
│ Error: Missing required provider
...
$ echo $?
1
```

**De l'autre, il en fait plus** : une fois les schémas en place, il attrape un
attribut qui n'existe dans aucun d'eux. Ce n'est pas de la syntaxe, c'est du
sens.

```hcl
resource "null_resource" "sonde" {
  attribut_qui_n_existe_dans_aucun_schema = true
}
```

```console
$ terraform validate
│ Error: Unsupported argument
$ echo $?
1
```

Ce qu'il ne fait toujours pas : joindre un provider, lire un état, ou dire si
votre infrastructure existe. Pour cela il faut `plan`.

## `fmt -check` rend 3, et cela se paie en CI

C'est le fait le plus utile de ce lab, et le moins connu. Un fichier hors
format canonique fait sortir `fmt -check` en **3**, pas en 1.

```console
$ terraform fmt -check -recursive ; echo $?
versions.tf
3
```

Un contrôle de CI écrit ainsi ne mesure donc rien :

```bash
terraform fmt -check -recursive
if [ $? -eq 1 ]; then
  echo "format non conforme"   # ne se déclenche jamais : le code vaut 3
fi
```

La forme juste ne teste pas un code particulier, elle teste **zéro** :

```bash
terraform fmt -check -recursive
```

et laisse le code non nul faire échouer l'étape.

## `plan -detailed-exitcode` a trois réponses, pas deux

| Code | Ce qu'il dit |
| --- | --- |
| **0** | rien à faire, l'infrastructure correspond à la configuration |
| **1** | la commande a échoué |
| **2** | le plan est réussi, et il contient des changements |

C'est le seul moyen de distinguer « ça a marché, rien à faire » de « ça a
marché, il y a du travail », sans lire un message destiné à un humain. Un
script qui teste seulement `!= 0` traite une dérive comme une panne.

## La cascade de précédence, dans l'ordre

Quand plusieurs sources posent la même variable, la **dernière chargée** gagne :

1. le `default` de la variable, quand personne d'autre ne parle ;
2. la variable d'environnement `TF_VAR_<nom>` ;
3. `terraform.tfvars` ;
4. `terraform.tfvars.json` ;
5. les `*.auto.tfvars`, par ordre alphabétique ;
6. `-var` et `-var-file`, dans l'ordre de la ligne de commande.

Retenir la liste ne suffit pas : le lab pose **chaque variable par plusieurs
sources à la fois**, et demande quatre outputs qui disent laquelle a gagné.
C'est là qu'on découvre qu'une variable d'environnement perd contre un simple
`terraform.tfvars`, ce que l'intuition place souvent dans l'autre sens.

## Renommer, adopter, rendre : trois blocs qui ne se ressemblent pas

**`moved`** renomme une ressource dans l'état sans rien détruire. Il ne suffit
pas de l'écrire : tant qu'il n'est pas **appliqué**, l'ancienne adresse reste.

```hcl
moved {
  from = random_pet.ancien_nom
  to   = random_pet.nouveau_nom
}
```

**`import`** fait passer sous gestion un objet qui existait déjà. Le test du
lab ne regarde pas l'adresse mais l'**identifiant** : une ressource créée
plutôt qu'importée en porte un autre, et c'est la seule preuve qui tienne.

```hcl
import {
  to = terraform_data.provisionne_ailleurs
  id = "identifiant-connu"
}
```

**`removed`** retire de l'état, et c'est ici que se trouve le piège le plus
coûteux du lot :

```hcl
removed {
  from = local_file.adopte

  lifecycle {
    destroy = false   # sans cette ligne, le fichier est DETRUIT
  }
}
```

Un mot d'écart entre « rendre un objet » et « le supprimer ».

## `-replace` remplace une ressource que rien n'obligeait à bouger

`terraform plan -replace=null_resource.a_remplacer -out=plan.tfplan` produit un
plan où cette adresse porte `["delete", "create"]`, et où **rien d'autre ne
bouge**. Si d'autres ressources apparaissent dans le plan, la configuration
n'avait pas convergé avant : ce n'est plus un remplacement, c'est un
rattrapage.

## `sensitive` cache un affichage, il ne chiffre rien

```console
$ terraform output
identifiant_sensible = <sensitive>
```

```console
$ jq '.outputs.identifiant_sensible' terraform.tfstate
{
  "sensitive": true,
  "value": "innocent-buck"
}
```

La valeur est **en clair dans l'état**. C'est pourquoi la vraie question n'est
jamais « ai-je marqué cet output sensible » mais « où mon état est-il stocké,
et qui peut le lire ». Le dernier test du lab exige les deux constats à la
fois.

## À vous de jouer

```bash
dsoxlab run certifications-associate-essential-commands
dsoxlab check certifications-associate-essential-commands
dsoxlab hint certifications-associate-essential-commands
```

Il se joue **hors ligne**, avec les providers `local`, `null` et `random` :
aucune VM, aucun compte cloud.

Les six codes ont été mesurés sur **Terraform v1.16.1** le 2026-09-24. Les
tests les rejouent sur votre configuration plutôt que de les croire sur parole :
si une version future en change un, c'est le lab qui sera déclaré à remesurer,
et non votre travail qui sera recalé.

Sous-objectif d'examen visé : **1b**.

Référence : [préparer la certification Terraform Associate](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/certifications/associate/)
