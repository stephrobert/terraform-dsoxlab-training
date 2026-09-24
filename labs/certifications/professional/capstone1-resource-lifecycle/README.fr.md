# Reprendre en main ce qu'on n'a pas créé

C'est le premier objectif du Professional, le seul pour lequel HashiCorp publie
des practice labs officiels, et le plus discriminant. Écrire une configuration
neuve s'apprend en un après-midi. Reprendre une infrastructure qui existe déjà,
que personne n'a documentée et que Terraform ignore, est le quotidien du métier.

Le lab se joue sur **Floci**, un émulateur AWS local : aucun compte, aucune
facture. Deux objets ont été créés **hors Terraform**, à la main : une instance
EC2 et un bucket S3.

## Un import n'est pas fini quand la ressource est dans le state

C'est le contresens qui coûte le plus cher, et le lab en fait son critère
central.

```console
$ terraform state list
aws_instance.facturation      # elle y est
$ terraform plan -detailed-exitcode
  ~ instance_type = "t3.micro" -> "t3.small"
$ echo $?
2
```

La ressource est bien dans le state, et pourtant l'import est **raté** : votre
configuration décrit autre chose que l'objet réel. Le prochain `apply` modifiera
cet objet, en production, sans que personne l'ait demandé.

Le critère de réussite est donc :

```console
$ terraform plan -detailed-exitcode
No changes.
$ echo $?
0
```

Ce qui impose de **relever les valeurs réelles** avant d'écrire la
configuration, plutôt que d'écrire ce qu'on aurait mis.

## Deux types d'objets, deux façons de les nommer

L'identifiant d'un import n'est pas une convention Terraform, c'est celui du
**fournisseur**, et il change avec le type :

| Ressource | Identifiant d'import |
| --- | --- |
| `aws_instance` | l'identifiant de l'instance, `i-0abc...` |
| `aws_s3_bucket` | le **nom** du bucket |

Et personne ne vous les tend : les retrouver est la première étape.

```bash
aws --endpoint-url http://localhost:14566 ec2 describe-instances \
    --filters 'Name=tag:Name,Values=capstone-facturation' \
    --query 'Reservations[].Instances[].InstanceId' --output text
```

## La dérive est une information, pas une faute

Quelqu'un a changé un tag à la main. Le plan propose de le remettre. Le réflexe
est d'appliquer, parce que « le code fait foi ».

Mais une dérive dit que **quelqu'un a fait quelque chose**, pour une raison
qu'on ignore. L'écraser efface le changement et la raison. Le lab demande donc
de l'**accepter** : aligner le code sur la réalité.

Deux codes de retour tombent alors ensemble, et il faut les deux :

```console
$ terraform plan -detailed-exitcode                 # 0 : le réel colle au code
$ terraform plan -refresh-only -detailed-exitcode   # 0 : le state colle au réel
```

Le premier seul ne suffit pas : il peut sortir en **0** sur un state périmé,
parce qu'il compare le code à ce que le state croit, et non à ce qui est.

## Ce qui est arrivé en écrivant ce lab

Deux mesures qui valent au-delà de lui.

**L'objet hérité n'existe pas tout de suite.** Il est créé au démarrage du
service, en parallèle du lab. La solution de référence, lancée aussitôt après
`dsoxlab run`, ne trouvait rien et sortait en erreur, alors qu'elle passait
relancée à la main dix secondes plus tard. Un geste qui attend un effet attend
cet effet, avec un budget borné.

**Un conteneur oublié bloque la création suivante.** Floci démarre un vrai
conteneur derrière chaque instance, et lui attribue un port SSH. Des conteneurs
laissés par une session interrompue occupent ces ports, et l'instance suivante
échoue sur `Bind for 0.0.0.0:2201 failed: port is already allocated`, un message
qui ne parle ni d'instance ni de lab. C'est pourquoi le dernier test détruit
**quoi qu'il arrive**.

## À vous de jouer

```bash
dsoxlab run certifications-professional-capstone1-resource-lifecycle
dsoxlab check certifications-professional-capstone1-resource-lifecycle
dsoxlab hint certifications-professional-capstone1-resource-lifecycle
```

Cinq tests. Aucun ne lit votre `.tf` : ils interrogent le state, le plan, et
Floci directement. Le dernier détruit et exige que **rien ne survive**, ni dans
le state ni chez le fournisseur.

Objectif d'examen visé : **1**, et surtout **1e**.

Référence : [le programme du Terraform Authoring and Operations Professional](https://developer.hashicorp.com/terraform/tutorials/pro-cert/pro-review)
