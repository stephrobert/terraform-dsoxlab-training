# count, for_each et le piège de l'index positionnel

Les meta-arguments **`count`** et **`for_each`** créent plusieurs instances d'une
même ressource. Ils se ressemblent, mais un détail les sépare et cause des
destructions parasites : `count` indexe ses instances par un **entier**,
`for_each` par une **clé**. Ce tutoriel montre la différence sur un exemple
**jetable** de panneaux, le piège du décalage d'index, le `count` conditionnel,
et la migration `count` vers `for_each` sans rien détruire. Le challenge, lui,
vous fera choisir le bon meta-argument sur un autre cas.

La preuve se lit toujours dans le **plan JSON** (`terraform show -json`), jamais
dans la sortie humaine, qui se lit trop vite.

## count : un nombre de copies, indexées par entier

`count = N` crée `N` instances identiques, adressées `ressource.nom[0]`,
`ressource.nom[1]`, etc. L'index courant est `count.index`, et il démarre à
**0** :

```hcl
resource "local_file" "copie" {
  count    = 3
  filename = "${path.module}/copie-${count.index}.txt"
  content  = "exemplaire ${count.index}\n"
}
```

`count` attend une valeur **connue avant l'apply** : elle ne peut pas dépendre
d'un attribut qui n'existe qu'une fois la ressource créée.

## for_each : une instance par clé

`for_each` prend une **map** ou un **set**, et crée une instance par élément,
adressée par la **clé** : `ressource.nom["nord"]`. Dans le bloc, `each.key`
donne la clé courante et `each.value` la valeur :

```hcl
resource "local_file" "panneau" {
  for_each = toset(["nord", "sud", "est"])
  filename = "${path.module}/panneau-${each.key}.txt"
  content  = "zone ${each.key}\n"
}
```

Un même bloc ne peut pas porter les deux : `count` **et** `for_each` ensemble
lèvent `Error: Invalid combination of "count" and "for_each"`.

## Le piège : l'index positionnel de count

Voici la raison d'être de tout ce tutoriel. Avec `count`, l'identité d'une
instance est sa **position**. Retirez un élément du **milieu** d'une liste, et
tout ce qui suit **se décale d'un cran**. Terraform ne voit pas « un élément a
disparu », il voit « l'instance à cet index a changé de contenu ».

```hcl
variable "zones" {
  type    = list(string)
  default = ["nord", "sud", "est"]
}

resource "local_file" "borne" {
  count    = length(var.zones)
  filename = "${path.module}/borne-${var.zones[count.index]}.txt"
  content  = "zone=${var.zones[count.index]}\n"
}
```

Appliquez avec les trois zones, puis retirez `sud` (celle du milieu). Le plan
JSON est sans appel :

```bash
terraform plan -out=tfplan -var 'zones=["nord","est"]'
terraform show -json tfplan | jq -c '.resource_changes[] | {address, actions: .change.actions}'
```

```json
{"address":"local_file.borne[0]","actions":["no-op"]}
{"address":"local_file.borne[1]","actions":["delete","create"]}
{"address":"local_file.borne[2]","actions":["delete"]}
```

`borne[1]` (qui portait `sud`) est **détruite et recréée** avec `est`, et
`borne[2]` est **détruite**. Retirer une zone en a fait recréer une autre. Sur
un fichier, c'est indolore ; sur une base de données ou un volume, c'est un
incident.

## for_each n'a pas ce piège

Les mêmes zones, mais keyées par nom. Retirez `sud` : Terraform ne touche que
`sud`, parce que l'identité est la **clé**, pas la position.

```hcl
resource "local_file" "borne" {
  for_each = toset(var.zones)
  filename = "${path.module}/borne-${each.key}.txt"
  content  = "zone=${each.key}\n"
}
```

```json
{"address":"local_file.borne[\"nord\"]","actions":["no-op"]}
{"address":"local_file.borne[\"sud\"]","actions":["delete"]}
{"address":"local_file.borne[\"est\"]","actions":["no-op"]}
```

D'où la règle officielle : `count` quand les instances sont **interchangeables**
(un nombre de copies identiques) ; `for_each` dès qu'elles ont une **identité
propre** que l'ajout ou le retrait de l'une ne doit pas déplacer.

## count conditionnel : 0 ou 1 instance

Le seul usage vraiment courant de `count` reste le **on/off** : une ressource
présente ou absente selon un booléen, avec le pattern `count = condition ? 1 : 0`.

```hcl
variable "affichage" {
  type    = bool
  default = false
}

resource "local_file" "banniere" {
  count    = var.affichage ? 1 : 0
  filename = "${path.module}/banniere.txt"
  content  = "promo\n"
}
```

À `false`, aucune instance n'existe. Passer de 0 à 1 crée `banniere[0]` et **ne
détruit rien d'autre** : c'est un mythe tenace que « count 0 vers 1 » détruirait
les voisins.

Pour exposer l'attribut d'une ressource qui a 0 ou 1 instance, la liste splat
`banniere[*].id` a une longueur 0 ou 1. La fonction **`one()`** la réduit à une
valeur unique, ou `null` si elle est vide :

```hcl
output "banniere_id" {
  value = one(local_file.banniere[*].id)
}
```

Une sortie dont la valeur est `null` est simplement **omise** de
`terraform output`, ce qui est le comportement attendu quand l'affichage est
désactivé.

## Migrer de count vers for_each sans rien détruire

C'est le point qui sépare l'usage débutant de l'usage professionnel. Vous avez
appliqué une ressource en `count`, vous voulez passer à `for_each` pour tuer le
piège de l'index. Changer le bloc **sans précaution** détruit tout et recrée
tout : les adresses passent de `borne[0]` à `borne["nord"]`, et Terraform ne
devine pas la correspondance.

Le bloc **`moved`** la lui donne :

```hcl
resource "local_file" "borne" {
  for_each = toset(var.zones)
  filename = "${path.module}/borne-${each.key}.txt"
  content  = "zone=${each.key}\n"
}

moved {
  from = local_file.borne[0]
  to   = local_file.borne["nord"]
}

moved {
  from = local_file.borne[1]
  to   = local_file.borne["sud"]
}

moved {
  from = local_file.borne[2]
  to   = local_file.borne["est"]
}
```

Le plan devient **entièrement no-op**, et chaque changement d'adresse est tracé
dans le JSON par `previous_address` :

```bash
terraform show -json tfplan | jq -c '.resource_changes[] | {address, prev: .previous_address, actions: .change.actions}'
```

```json
{"address":"local_file.borne[\"nord\"]","prev":"local_file.borne[0]","actions":["no-op"]}
```

Un cas plus simple se gère **tout seul** depuis les versions récentes : ajouter
`count = 1` à une ressource qui n'en avait pas migre `borne` vers `borne[0]`
sans destruction (`# ... has moved to ...`, `0 to destroy`). Mais dès qu'il faut
deviner des **clés**, comme pour `for_each`, le bloc `moved` est obligatoire.

## À vous de jouer

Vous savez que `count` indexe par entier et `for_each` par clé, que le décalage
d'index de `count` recrée les instances suivantes, que `count = cond ? 1 : 0`
avec `one()` gère l'optionnel, et que `moved` migre sans détruire. Le challenge
vous fait choisir le bon meta-argument pour chaque ressource, et les tests
prouvent le comportement dans le plan JSON, y compris le non-piège au retrait.

```bash
dsoxlab run write-code-count
dsoxlab check write-code-count
dsoxlab hint write-code-count
```

Sous-objectifs d'examen visés : **4b** (Terraform Associate, meta-arguments) et
la migration par `moved` du niveau Professional.

Référence : [count et for_each en Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/count-terraform/)
