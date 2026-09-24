# Mettre d'accord fmt, validate et les outputs

Un lab qui vérifierait que des commandes ont été tapées ne prouverait rien. Ce
qui se prouve, c'est qu'une **chaîne non interactive** traverse la configuration
sans qu'un humain ait à lire une seule sortie formatée pour lui.

C'est exactement ce que fait une CI, et c'est là que la CLI Terraform révèle
qu'elle a deux visages : celui qu'elle montre à l'écran, et celui qu'elle réserve
aux scripts.

## Toute commande utile a un mode machine

| Commande | Sortie pour un humain | Sortie pour un script |
| --- | --- | --- |
| `fmt` | la liste des fichiers | le **code retour** |
| `validate` | un texte encadré | `validate -json` |
| `plan` | un diff coloré | `plan -out` puis `show -json` |
| `output` | `clé = valeur` | `output -json` |
| `show` | un état lisible | `show -json` |

La règle générale : **ne parsez jamais ce qui est écrit pour être lu**. Un
texte change avec les versions, une couleur disparaît quand la sortie n'est pas
un terminal, et un tableau se réaligne. Le JSON et les codes retour, non.

## `validate -json` répond en structure

```console
$ terraform validate -json | jq '{valid, error_count, warning_count}'
{
  "valid": false,
  "error_count": 1,
  "warning_count": 0
}
```

Deux choses utiles ici. D'abord `valid` est un booléen, pas une phrase à
reconnaître. Ensuite **les avertissements sont comptés à part** : une
configuration peut être valide et porter des avertissements, et c'est à votre
script de décider s'il les tolère.

Et le prérequis qu'on oublie : `validate` a besoin des **schémas des
providers**. Lancé avant `init`, il échoue pour une raison étrangère à la
qualité du code.

## Les outputs sont le seul canal officiel vers un script

Une valeur qui n'est pas exposée en `output` n'est pas accessible à
l'extérieur, sauf à fouiller le state, ce qui revient à dépendre d'un format
interne.

```console
$ terraform output -json | jq -r '.adresse.value'
```

C'est le contrat : la configuration décide de ce qu'elle publie, le script ne lit
que cela.

## `terraform console` marche sans terminal

Peu connu, et précieux : la console accepte une expression sur son **entrée
standard** et rend le résultat, sans session interactive.

```console
$ echo 'cidrhost("10.0.0.0/16", 5)' | terraform console
"10.0.0.5"
```

Cela permet de vérifier une expression HCL dans un script, ou de comprendre ce
que fait une fonction sans écrire un fichier jetable.

## Ne pas confondre les codes de `plan`

```bash
terraform plan -detailed-exitcode
```

| Code | Ce qu'il dit |
| --- | --- |
| **0** | aucun changement |
| **1** | erreur |
| **2** | des changements sont en attente |

Sans `-detailed-exitcode`, un plan qui a des changements rend **0** comme un plan
vide : la commande a réussi, voilà tout. C'est ce drapeau qui transforme `plan`
en test.

## À vous de jouer

```bash
dsoxlab run getting-started-cli-terraform
dsoxlab check getting-started-cli-terraform
dsoxlab hint getting-started-cli-terraform
```

Le lab se joue **hors ligne**, sur les providers `local`, `null` et `random`.
Trois défauts sont posés volontairement : un fichier hors format, une erreur de
validation, et des outputs manquants. Tout doit ensuite tourner **sans
confirmation interactive**.

Sous-objectif d'examen visé : **3c**, exécuter le workflow en automation.

Référence : [la CLI Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/decouvrir/cli-terraform/)
