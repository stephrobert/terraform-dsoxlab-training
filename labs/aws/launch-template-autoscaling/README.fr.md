# Lire un remplacement dans le plan, avant qu'il n'arrive

Deux idées reçues coûtent cher sur un groupe d'auto-scaling, et toutes deux
passent la revue de code sans encombre :

- `version = "$Latest"` sur le launch template d'un ASG ne déclenche **jamais**
  d'instance refresh ;
- un `create_before_destroy` posé sur le **launch template** ne protège rien du
  tout.

Ce lab les fait lire dans le plan converti en JSON, **sans jamais appeler AWS** :
aucun `apply`, aucun compte, pas même l'émulateur. Le state est fourni, tous les
plans se lancent avec `-refresh=false`, et seul le premier `init` a besoin du
réseau.

## Ce qui est connu au plan ne déclenche rien

C'est le cœur du premier piège, et il tient en une phrase : **une valeur connue
au moment du plan ne produit aucun changement**.

`"$Latest"` est une chaîne littérale. Elle vaut `"$Latest"` avant l'apply, et
encore après. Du point de vue de Terraform, rien n'a bougé : l'ASG reste en
`no-op`, le groupe n'est jamais rafraîchi, et personne ne s'en aperçoit avant
longtemps.

Omettre l'argument ne vaut pas mieux : il retombe sur `"$Default"`, avec le même
effet.

Il faut une valeur **calculée à l'apply**, c'est-à-dire une référence à
l'attribut du template :

```hcl
launch_template {
  id      = aws_launch_template.socle.id
  version = aws_launch_template.socle.latest_version
}
```

Cela se vérifie dans le plan, à un endroit qu'on lit rarement :

```console
$ terraform show -json plan.tfplan | jq '.resource_changes[]
    | select(.type=="aws_autoscaling_group") | .change.after_unknown'
```

`after_unknown` porte `true` sur ce que Terraform ne connaîtra qu'à l'apply.
C'est la preuve que la valeur est calculée, et non figée.

## Mettre à jour un template ne le remplace pas

Changer `image_id` sur un `aws_launch_template` **crée une version**. Le
template n'est pas remplacé : son plan porte `["update"]`.

C'est ce qui rend le second piège si naturel. On veut éviter une coupure, on
pose `create_before_destroy` sur la ressource qu'on vient de modifier, et on a
l'impression d'avoir traité le sujet. Mais la ressource remplacée, c'est le
**groupe**, pas le template.

```console
$ terraform show -json plan.tfplan | jq '.resource_changes[].change.actions'
["update"]              # le template
["create","delete"]     # le groupe
```

L'**ordre** de ces deux valeurs est exactement ce qui distingue
`create_before_destroy` du comportement par défaut :

| Actions | Ce qui se passe |
| --- | --- |
| `["delete", "create"]` | l'ancien part d'abord : **fenêtre à zéro instance** |
| `["create", "delete"]` | le nouveau arrive d'abord : pas de creux |

Et `replace_paths` nomme l'attribut qui a forcé le remplacement.

## Les deux exigences sont liées

`create_before_destroy` fait **coexister** deux groupes le temps de la bascule.
Or AWS refuse deux groupes portant le même nom.

Poser la règle sans changer le nom produit donc une collision, et traiter le nom
sans la règle laisse le creux de capacité. Les deux exigences ne se traitent pas
séparément, et c'est le genre de lien qu'un tutoriel ne mentionne pas parce qu'il
ne se voit qu'à l'exécution.

D'où le `keepers` du `random_integer` : c'est lui qui fait changer le suffixe
quand le template change, donc qui rend le nouveau nom **inconnu au plan**, donc
nécessairement différent de l'ancien.

## `instance_refresh` a un plafond par défaut qui bloque

Deux préférences, et il faut les deux :

- le **plancher** : ne jamais descendre sous la capacité cible ;
- le **plafond** : autoriser explicitement un dépassement.

Le second surprend. La valeur par défaut du plafond **refuse** de dépasser la
capacité cible ; sans le relever, il n'y a pas de place pour créer une instance
avant d'en retirer une, et le plancher demandé devient impossible à tenir.

## À vous de jouer

```bash
dsoxlab run aws-launch-template-autoscaling
dsoxlab check aws-launch-template-autoscaling
dsoxlab hint aws-launch-template-autoscaling
```

Huit tests, tous lus dans un plan écrit en binaire puis converti en JSON. Le
dernier exige que le plan **ne soit pas vide** : ici, un code de sortie 2 est le
succès, parce qu'un lab qu'on aurait neutralisé pour faire passer les tests
sortirait en 0.

Sous-objectif d'examen visé : **1b**.

Référence : [launch template et autoscaling](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/launch-template-autoscaling/)
