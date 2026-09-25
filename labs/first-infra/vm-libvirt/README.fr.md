# Mise à jour en place ou remplacement : le lire dans le plan

Modifier une machine virtuelle n'est pas une opération, c'en est deux. Selon
l'attribut touché, Terraform redéfinit la machine sans l'interrompre, ou la
détruit pour en fabriquer une autre. La différence se voit **avant** l'apply, à
condition de savoir où regarder, et elle se paie cher le jour où on l'apprend en
production.

## Le plan porte un verbe, pas une couleur

La sortie humaine met des `~` et des `-/+` que l'on survole. Le plan enregistré,
relu en JSON, porte un champ qui ne se survole pas :

```console
$ terraform plan -out=tfplan
$ terraform show -json tfplan | jq '.resource_changes[].change.actions'
["update"]
```

Trois valeurs suffisent à tout dire :

| `change.actions` | Ce qui va arriver |
| --- | --- |
| `["update"]` | mise à jour en place, la machine survit |
| `["delete", "create"]` | remplacement, la machine est refaite |
| `["create", "delete"]` | remplacement aussi, mais la nouvelle est créée d'abord (`create_before_destroy`) |

Quand il s'agit d'un remplacement, le plan dit aussi **quel attribut** l'a
forcé, au même endroit :

```json
"actions": ["delete", "create"],
"replace_paths": [["name"]]
```

Mesuré sur ce lab : `replace_paths` vaut `null` pour une mise à jour de la
mémoire ou des vCPU, et `[["name"]]` pour un changement de nom. C'est la réponse
à « qu'est-ce qui, dans ma modification, a forcé ça », et elle est dans le plan,
pas dans la documentation.

## Ce qui se modifie, et ce qui recrée

Sur un domaine libvirt, la frontière est nette et ce lab la fait constater dans
les deux sens :

- **la mémoire et les vCPU se modifient en place.** libvirt sait redéfinir un
  domaine sans le détruire ;
- **le nom force un remplacement.** Il *est* l'identité du domaine : le changer
  ne modifie pas la machine, il en fabrique une autre.

La règle générale derrière ce cas particulier : un attribut qui participe à
l'**identité** d'un objet chez le fournisseur ne peut pas être mis à jour. Le
provider le déclare `ForceNew`, et le plan le traduit en `delete` + `create`.

## L'identifiant tranche après coup

Une prédiction reste une prédiction. Ce qui prouve l'opération réellement subie,
c'est l'identifiant que libvirt attribue **à la création** :

```console
$ terraform show -json | jq -r '.values.root_module.resources[]
    | select(.type=="libvirt_domain") | .values.id'
```

Une machine modifiée garde le sien. Une machine remplacée en reçoit un autre.
Le lab relève les deux et les compare : c'est la seule façon de savoir si
l'outil a tenu la parole donnée par le plan.

## `running` ne prouve pas qu'une VM a booté

Mesure faite en écrivant le lab, et elle vaut au-delà de libvirt : une machine
sans disque bootable est `running` elle aussi. L'état « en marche » dit qu'un
processus existe, pas qu'un système a démarré.

Ce qui les distingue est le **temps CPU consommé** : de l'ordre de 0,3 seconde
pour une machine qui cherche vainement un disque, plusieurs secondes pour une
machine qui démarre vraiment.

C'est pourquoi le disque est un **dérivé en copie sur écriture** de l'image
cloud, et non un volume vierge : l'image n'est jamais modifiée, le disque de la
VM ne porte que les blocs qui changent, et recréer une machine coûte une seconde
au lieu de recopier 600 Mio.

## À vous de jouer

```bash
dsoxlab run first-infra-vm-libvirt
dsoxlab check first-infra-vm-libvirt
dsoxlab hint first-infra-vm-libvirt
```

**Prérequis** : `libvirt` joignable en `qemu:///system`, le pool `default` et le
réseau `default` utilisables, et l'image cloud présente :

```bash
mkdir -p /var/tmp/dsoxlab-images && curl -fsSL \
  -o /var/tmp/dsoxlab-images/noble-server-cloudimg-amd64.img \
  https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
```

La VM et son disque sont détruits en sortie, quoi qu'il arrive.

Sous-objectif d'examen visé : **1b**.

Référence : [créer une VM avec libvirt](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/vm-libvirt/)
