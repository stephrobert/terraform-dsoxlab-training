# Faire dire au plan ce qu'un changement de launch template fait vraiment

## La situation

**Sous-objectif d'examen visé : 1b.**

Un ASG qui référence `version = "$Latest"` ne déclenche jamais d'instance refresh, et un
`create_before_destroy` posé sur le launch template ne protège rien du tout. Ce lab fait lire ces
deux vérités dans le plan converti en JSON, sans jamais appeler AWS.

## Capacité visée

Faire dire à un plan, sur une infrastructure déjà appliquée, quelle ressource est mise à jour,
laquelle est remplacée et dans quel ordre le remplacement se fera, puis corriger la configuration
pour que le remplacement du groupe ne passe ni par une fenêtre à zéro instance, ni par une
collision de nom.

## D'où part l'apprenant

Note d'exécution : aucun compte AWS, aucun `apply`, et l'émulateur Floci n'est pas requis. Sa
couverture de `CreateLaunchTemplate` et de l'instance refresh n'a pas pu être vérifiée, donc le lab
ne repose sur aucun appel d'API : le provider est configuré avec des identifiants factices et ses
contrôles désactivés, et tous les plans se lancent avec `-refresh=false`. Seul le premier
`terraform init` a besoin du réseau. `challenge/work` contient :

- `versions.tf` : fourni, à ne pas modifier. Terraform `>= 1.11.0`, `hashicorp/aws` et
  `hashicorp/random` épinglés à une version exacte, bloc `provider "aws"` déjà neutralisé.
- `terraform.tfstate` : fourni. Un socle déjà en service : un `random_integer.suffixe`, un
  `aws_launch_template.socle` en version 1 sur `ami-0000000000000a1`, et un
  `aws_autoscaling_group.grappe` nommé `grappe-app-742`, min 2, max 4, cible 2, pointant la
  version `"1"` du template.
- `main.tf` : la configuration cible, trouée. L'AMI du template y est déjà passée à
  `ami-0000000000000b7`, c'est la demande métier. Valent `"???"` : l'argument `version` du bloc
  `launch_template` de l'ASG, l'argument qui donne son nom au groupe, le bloc `keepers` du
  `random_integer`, le bloc `lifecycle` de l'ASG et deux préférences d'`instance_refresh`.
- `CONSIGNES.md` : déployer la nouvelle AMI sans jamais descendre sous la capacité cible, et
  appliquer au groupe la nouvelle convention de nommage.

## L'état à atteindre

1. `aws_launch_template.socle` porte l'action `update` seule : changer `image_id` crée une
   version, cela ne remplace pas le template.
2. `aws_autoscaling_group.grappe` n'est pas un `no-op` : la version de template qu'il référence est
   inconnue au moment du plan, car calculée à l'apply. Un `"$Latest"` littéral, comme une omission
   de l'argument qui vaudrait alors `"$Default"`, produirait l'inverse.
3. Ce même ASG porte les actions `create` puis `delete`, dans cet ordre, et non l'inverse.
4. Le chemin de remplacement déclaré par le plan désigne le nom du groupe.
5. Le nom du nouveau groupe est lui aussi inconnu au moment du plan, donc nécessairement différent
   de `grappe-app-742` : les deux générations ne peuvent pas entrer en collision pendant la bascule.
6. `random_integer.suffixe` est remplacé dans ce même plan.
7. Les préférences d'`instance_refresh` interdisent toute descente sous la capacité cible et
   autorisent explicitement un dépassement, ce que la valeur par défaut du plafond refuse.
8. Le plan signale bien des changements en attente : rien n'a été neutralisé pour faire passer les
   tests.

## Comment on le prouve

Aucun test n'ouvre un fichier `.tf`. Le plan est écrit en binaire puis converti en JSON. Les points
1 et 3 se lisent dans `resource_changes[].change.actions` : `["update"]` pour le template,
`["create", "delete"]` pour le groupe, l'ordre des deux valeurs étant exactement ce qui distingue
`create_before_destroy` du comportement par défaut. Le point 4 se lit dans
`resource_changes[].change.replace_paths`. Les points 2 et 5 se lisent dans `change.after_unknown`,
où la version du template et le nom du groupe valent vrai alors qu'ils seraient des chaînes connues
dans une configuration figée. Le point 6 est un troisième `resource_changes` en remplacement, le
point 7 se lit dans `planned_values` sur les préférences imbriquées de l'ASG, et le point 8 vient du
code de sortie de `terraform plan -refresh=false -detailed-exitcode`, dont la valeur 2 est ici
l'attendu. Un `challenge/work` vide ne produit aucun `resource_changes` et échoue partout ; recopier
`"$Latest"` échoue sur le point 2 ; garder un nom figé échoue sur les points 5 et 6 ; retirer le
bloc `lifecycle` échoue sur le point 3.

## 🎯 Challenge : lire un remplacement dans le plan

### Point de départ

Un socle est **déjà en service**, décrit par le `terraform.tfstate` fourni :
un `aws_launch_template.socle` en version 1 sur `ami-0000000000000a1`, et un
`aws_autoscaling_group.grappe` nommé `grappe-app-742`, min 2, max 4, cible 2.

`challenge/work` contient `versions.tf` (**fourni**, provider neutralisé),
`terraform.tfstate` (**fourni**), `CONSIGNES.md` et `main.tf` (**troué**).

**Aucun `apply`, aucun compte AWS, aucun émulateur.** Tout se lit dans le plan,
et tous les plans se lancent avec `-refresh=false`. Seul le premier
`terraform init` a besoin du réseau.

### ✅ Objectif

L'AMI est déjà passée à `ami-0000000000000b7` : c'est la demande métier. Il
reste cinq `???`, et chacun décide d'un comportement que le plan révélera.

1. Le `keepers` du `random_integer`.
2. L'argument qui donne son **nom** au groupe.
3. L'argument `version` du bloc `launch_template` de l'ASG.
4. Le bloc `lifecycle` de l'ASG.
5. Les **deux** préférences d'`instance_refresh`.

### 🧭 Les deux pièges, et pourquoi ils ne se voient pas

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

### 🔍 Validation

```bash
dsoxlab check aws-launch-template-autoscaling
```

Huit tests. Le plan est écrit en binaire puis converti en JSON. L'ordre des
actions, `["create", "delete"]` et non l'inverse, est exactement ce qui
distingue `create_before_destroy` du comportement par défaut. Les valeurs
inconnues se lisent dans `after_unknown`, le déclencheur du remplacement dans
`replace_paths`. Le dernier test exige que le plan **ne soit pas vide** : ici,
un code de sortie 2 est le succès. Aucun test n'ouvre un `.tf`.
