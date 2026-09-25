# Un examen blanc dont les réponses se prouvent

Un QCM corrigé à la main ne prouve rien, et se triche tout seul. On coche, on
regarde le corrigé, on se dit qu'on savait. Le jour de l'examen, la question
porte sur ce qu'une commande **refuse** de faire, et l'illusion tombe.

Ce lab corrige deux défauts d'un examen blanc ordinaire, et ce sont eux qui
justifient son existence.

## Les réponses voyagent dans un fichier de variables

Vous ne cochez pas, vous **déclarez** :

```hcl
reponses = {
  q01 = "b"
  q02 = "ac"
  ...
}
```

Terraform corrige lui-même, et rend le résultat en JSON :

```console
$ terraform output score
87
$ terraform output score_par_objectif
{ "1" = 100, "2" = 75, "3" = 85, ... }
```

Le barème ne porte **aucune réponse en clair**, seulement l'empreinte `sha256`
salée de chacune.

Disons tout de suite ce que cela vaut : cela empêche de **lire** les réponses en
ouvrant un fichier, ce qui est le cas réel. Cela n'empêche pas de les
**retrouver**, puisque le sel est dans le barème et qu'une question à choix
unique n'a que quatre réponses possibles. Aucun barème local ne peut faire
mieux, et il vaut mieux l'écrire que de laisser croire à une inviolabilité.

## Quatre questions n'ont de réponse qu'après avoir construit

C'est le vrai garde-fou, et c'est ce qui distingue ce lab d'un questionnaire.

Les quatre dernières questions portent sur l'**état** d'un atelier Terraform que
vous devez monter : combien d'objets en `mode: managed`, quelle est l'adresse du
seul bloc en `mode: data`, quel code rend `plan -detailed-exitcode` après
l'apply, et si la valeur sensible se lit en clair dans le state.

Les tests **recalculent** ces quatre valeurs depuis votre propre état, puis les
confrontent aux empreintes. Deux conséquences :

- répondre sans construire échoue sur l'état ;
- construire sans répondre échoue sur le score.

Les deux moitiés du lab se tiennent l'une l'autre.

## L'atelier ramasse ce que le programme a de moins récitable

Il tient en quatre ressources et un bloc `data`, et pourtant il fait poser côte
à côte cinq mécanismes qu'on confond :

| Ce qu'il faut écrire | Ce que cela fait constater |
| --- | --- |
| `create_before_destroy` | l'ordre du remplacement, lisible dans le plan |
| `precondition` | un refus **au plan**, avant toute action |
| `postcondition` | la relecture du résultat par `self`, la seule qui en dispose |
| bloc `check` | le seul des cinq qui **avertit sans bloquer** |
| `depends_on` | la seule dépendance qu'aucune référence ne peut exprimer |

Et une sortie sensible, qui fait constater que `sensitive` masque un affichage
sans rien chiffrer : la valeur est en clair dans `terraform.tfstate`.

## Le seuil, et pourquoi il y en a deux

Le lab exige **80 % au global** et **50 % par objectif**.

Le second n'est pas une sévérité gratuite. Quarante questions permettent de
compenser : on peut rater un objectif entier et rester à 82 % en étant bon
partout ailleurs. Un score global flatteur cache alors un pan du programme
jamais révisé, qui tombera le jour de l'examen. Le plancher par objectif
interdit l'impasse.

```console
$ terraform output score_par_objectif
{ "1" = 100, "2" = 75, "3" = 85, "4" = 90, "5" = 25, "6" = 80, "7" = 100, "8" = 100 }
```

Ici le global passe, le lab échoue, et il dit où réviser.

## À vous de jouer

```bash
dsoxlab run certifications-associate-mock-004
dsoxlab check certifications-associate-mock-004
dsoxlab hint certifications-associate-mock-004
```

Il se joue **hors ligne**, avec les providers `local`, `null` et `random` :
aucune VM, aucun compte cloud.

Les quarante questions sont étiquetées par **sous-objectif officiel**, lus le
2026-09-24 dans la grille publiée par HashiCorp et conservés dans le
`curriculums.yml` du dépôt.

Un mot sur la couverture : l'objectif **4h** parle de gestion des secrets, et
`local`, `null` et `random` n'offrent aucun argument *write-only*. Ce
sous-objectif est donc éprouvé autrement, par une question de cours et par une
question d'atelier qui fait constater la valeur sensible en clair dans le state.

Objectif visé : les **huit** du programme Associate 004.

Référence : [préparer la certification Terraform Associate](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/certifications/associate/)
