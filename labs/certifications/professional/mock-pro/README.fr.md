# Six objectifs, six répertoires, une seule séance

Les six capstones de la section Professional éprouvent un objectif chacun, et
c'est ce qu'il faut pour apprendre. L'examen, lui, ne prévient pas de quel
objectif relève la tâche suivante, et il ne laisse pas le temps de se replacer.

Ce lab est la répétition générale : six tâches, une par objectif, à jouer d'une
traite une fois les capstones réussis.

## Ce qu'il change par rapport aux capstones

**Rien n'est annoncé au bon moment.** Chaque répertoire porte ses consignes en
commentaire, comme une reprise de dépôt existant, et la difficulté est autant
dans la lecture que dans l'écriture. Trois tâches exigent en plus un plan
**stable** après travail : une solution qui reconstruit à chaque passage rend le
bon fichier et échoue quand même, ce qui est exactement ce que l'examen
sanctionne.

| Tâche | Objectif | Ce qui se mesure |
| --- | --- | --- |
| `t1-derive` | 1 | le fichier corrigé à la main est adopté, pas écrasé |
| `t2-dynamique` | 2 | trois fautes réparées, trois ressources devenues une, un port refusé au plan |
| `t3-etats` | 3 | la valeur traverse deux états, et suit quand le socle change |
| `t4-module` | 4 | trois environnements passent par un module, aucun objet recréé |
| `t5-providers` | 5 | le privé est rendu par une autre configuration, et les droits sont fermés |
| `t6-hcp` | 6 | douze questions, un seuil global, quatre sous-objectifs couverts |

## Deux pièges qui ne s'inventent pas

**Le premier est le contenu.** La tâche 1 pose un fichier que quelqu'un a
corrigé à la main. Une configuration qui le décrit approximativement donne un
state qui a l'air juste, un plan qui a l'air stable, et un fichier réécrit : la
correction est perdue. Seule la lecture du contenu distingue les deux, et c'est
ce que fait le test.

**Le second est la place des droits.** Le provider `local` n'accepte aucun
argument : son schéma de configuration est vide, mesuré le 2026-09-25. Y poser
`directory_permission` fait échouer l'apply sur

```
An argument named "directory_permission" is not expected here.
```

Les droits appartiennent à la ressource, et il y en a deux : un pour le fichier,
un pour le répertoire que Terraform crée au passage.

## La tâche 6 se corrige toute seule

Douze questions, un barème fourni qui ne porte **aucune réponse en clair**,
seulement l'empreinte `sha256` salée de chacune. Terraform rend le score, le
score par sous-objectif et la liste des questions sans réponse :

```console
$ terraform output score
83
$ terraform output score_par_sous_objectif
{ "6a" = 100, "6b" = 75, "6c" = 66, "6d" = 100 }
```

Il faut atteindre le seuil global **et** avoir répondu dans les quatre
sous-objectifs. Un score flatteur obtenu en séchant un pan du programme ne passe
pas : c'est la même exigence que dans `mock-004`, et pour la même raison.

Ce que le barème protège, disons-le : il empêche de **lire** les réponses en
ouvrant un fichier. Il n'empêche pas de les **retrouver**, puisque le sel y
figure et qu'une question à choix unique n'a que quatre réponses possibles.
Aucun barème local ne peut faire mieux.

## Ce qu'il ne couvre pas

Les providers locaux ne savent pas importer : `local` et `null` répondent tous
deux `Resource Import Not Implemented`. L'import reste éprouvé par
`capstone1-resource-lifecycle` et `aws-import-moved-drift`, qui ont un vrai
provider ; la tâche 1 éprouve ici l'autre moitié du même sous-objectif, la
réconciliation d'une dérive.

C'est le prix d'un examen blanc qui se lance d'un trait, sans émulateur ni
compte, et qui peut donc se rejouer autant de fois qu'il le faut.

## À vous de jouer

```bash
dsoxlab run certifications-professional-mock-pro
dsoxlab check certifications-professional-mock-pro
dsoxlab hint certifications-professional-mock-pro
```

Objectif visé : les **six** du programme Professional.

Référence : [Exercices Professional](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/certifications/professional/exercices/)
