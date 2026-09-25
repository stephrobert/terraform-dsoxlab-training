# 🎯 Challenge : reprendre après un apply qui a échoué

## Point de départ

`challenge/work` contient une configuration qui **a déjà échoué**, et son state
est fourni. Aucun cloud, aucune VM, aucun accès réseau : l'échec est
**déterministe** et se reproduit à l'identique sur n'importe quel poste.

Regardez le state avant de toucher à quoi que ce soit :

```bash
terraform show -json | jq '.values.root_module.resources[] | {address, tainted}'
```

## 🧭 Ce que le state dit vraiment

La ressource fautive **n'est pas absente** du state. Elle y figure, marquée
`tainted` : Terraform sait qu'elle est dans un état douteux et la **remplacera**
au prochain apply. C'est une nuance qu'on lit rarement, et elle change la façon
de reprendre.

Deux ressources sur trois sont **parfaitement saines**. Le réflexe de tout
détruire pour repartir de zéro est exactement ce que ce lab veut vous faire
perdre.

## ✅ Objectif

Corrigez **la cause** dans la configuration.

Ce qu'il ne faut pas faire, et qui vient à l'esprit en premier :

| Réflexe | Pourquoi c'est faux |
|---|---|
| supprimer la ressource fautive | l'échec disparaît, le besoin aussi |
| la commenter | idem, avec un souvenir dans le dépôt |
| `mkdir` à la main | la configuration reste fausse : elle échouera ailleurs |
| `terraform destroy` puis tout refaire | détruit deux ressources saines pour en réparer une |

## 🔍 Validation

```bash
dsoxlab check first-infra-debug-apply
```

Cinq tests. Le cœur du lab est **l'empreinte de reprise** : les identifiants des
ressources déjà créées sont comparés à ceux du state fourni. Toute valeur
différente signe une destruction suivie d'une recréation — l'état final serait
correct, mais le travail aurait été **refait** au lieu d'être repris. Sur un
fichier local cela ne coûte rien ; sur une base de données, cela coûte les
données.

Le dernier test rejoue votre configuration dans un répertoire **vierge**. Un
`mkdir` lancé à la main fait passer l'apply chez vous et nulle part ailleurs.
