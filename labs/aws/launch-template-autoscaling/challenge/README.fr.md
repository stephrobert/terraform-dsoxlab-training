# 🎯 Challenge : lire un remplacement dans le plan

## Point de départ

Un socle est **déjà en service**, décrit par le `terraform.tfstate` fourni :
un `aws_launch_template.socle` en version 1 sur `ami-0000000000000a1`, et un
`aws_autoscaling_group.grappe` nommé `grappe-app-742`, min 2, max 4, cible 2.

`challenge/work` contient `versions.tf` (**fourni**, provider neutralisé),
`terraform.tfstate` (**fourni**), `CONSIGNES.md` et `main.tf` (**troué**).

**Aucun `apply`, aucun compte AWS, aucun émulateur.** Tout se lit dans le plan,
et tous les plans se lancent avec `-refresh=false`. Seul le premier
`terraform init` a besoin du réseau.

## ✅ Objectif

L'AMI est déjà passée à `ami-0000000000000b7` : c'est la demande métier. Il
reste cinq `???`, et chacun décide d'un comportement que le plan révélera.

1. Le `keepers` du `random_integer`.
2. L'argument qui donne son **nom** au groupe.
3. L'argument `version` du bloc `launch_template` de l'ASG.
4. Le bloc `lifecycle` de l'ASG.
5. Les **deux** préférences d'`instance_refresh`.

## 🧭 Les deux pièges, et pourquoi ils ne se voient pas

**`version = "$Latest"` ne déclenche jamais rien.** C'est le réflexe, et c'est
faux : cette chaîne est **connue** au moment du plan, donc l'ASG reste en
`no-op`. Le groupe ne sera jamais rafraîchi, et personne ne s'en apercevra avant
longtemps. Omettre l'argument ne vaut pas mieux : il retombe sur `"$Default"`,
avec le même effet. Il faut une valeur **calculée à l'apply**.

**Un `create_before_destroy` posé sur le launch template ne protège rien.**
C'est le groupe qui est remplacé, pas le template — lui est simplement mis à
jour. Poser la règle au mauvais endroit donne l'illusion d'avoir traité le
sujet.

Et les deux exigences du métier sont **liées** : `create_before_destroy` fait
coexister deux groupes le temps de la bascule, or AWS refuse deux groupes de
même nom. C'est pour cela que le nom doit changer. Traiter l'une sans l'autre ne
marche pas.

## 🔍 Validation

```bash
dsoxlab check aws-launch-template-autoscaling
```

Huit tests. Le plan est écrit en binaire puis converti en JSON. L'ordre des
actions, `["create", "delete"]` et non l'inverse, est exactement ce qui
distingue `create_before_destroy` du comportement par défaut. Les valeurs
inconnues se lisent dans `after_unknown`, le déclencheur du remplacement dans
`replace_paths`. Le dernier test exige que le plan **ne soit pas vide** : ici,
un code de sortie 2 est le succès. Aucun test n'ouvre un `.tf`.
