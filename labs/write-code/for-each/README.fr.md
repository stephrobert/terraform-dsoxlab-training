# Ajouter une instance sans détruire les autres

Le vrai sujet de `for_each` n'est pas sa syntaxe, c'est ce qu'il **évite**. Avec
`count`, insérer une entrée au milieu d'une liste décale tous les index suivants,
et Terraform détruit puis recrée des ressources qui n'avaient aucune raison de
bouger. En production, c'est une coupure.

Ce tutoriel enseigne le mécanisme sur un exemple **jetable** : une poignée de
buckets de logs. Le challenge, lui, vous fera migrer un autre décor de `count`
vers `for_each` sans rien casser. Le lab tourne sur `random`, sans cloud.

## Prérequis

- `terraform` sur le PATH, version **1.1 ou plus récente** (les blocs `moved`
  n'existent pas avant).
- Un accès réseau pour le premier `terraform init`.

## Pourquoi count est fragile

`count` adresse les instances par **position** : `[0]`, `[1]`, `[2]`. Cette
position n'a aucun sens métier, elle dépend uniquement de l'ordre de la liste.
Montez deux buckets :

```hcl
variable "buckets" {
  type    = list(string)
  default = ["app", "audit"]
}

resource "random_pet" "bucket" {
  count  = length(var.buckets)
  length = 2
}
```

Après `apply`, l'état les nomme par rang :

```bash
terraform state list
```

```text
random_pet.bucket[0]
random_pet.bucket[1]
```

Insérez un bucket en première position et tout glisse : ce qui était `[0]`
devient `[1]`, ce qui était `[1]` devient `[2]`. Terraform ne voit pas un
décalage, il voit que l'instance `[0]` doit maintenant porter d'autres valeurs.
Il la **modifie ou la remplace**, en cascade.

## for_each adresse par clé

`for_each` remplace la position par une **clé stable**. L'instance de `app`
s'appelle `["app"]`, et gardera ce nom quelle que soit sa place dans la liste :

```hcl
resource "random_pet" "bucket" {
  for_each = toset(var.buckets)
  length   = 2
}
```

Deux contraintes que Terraform impose :

- `for_each` accepte une **map** ou un **set de chaînes**, jamais une liste. D'où
  le `toset()`.
- Les clés doivent être **connues au moment du plan**. Une clé dérivée d'un
  attribut de ressource non encore créée fait échouer le plan.

Dans le corps de la ressource, `count.index` laisse la place à `each.key` et
`each.value`.

## Migrer sans détruire : les blocs moved

Passer de `count` à `for_each` change l'**adresse** des instances dans l'état.
Sans rien d'autre, Terraform conclut que les anciennes adresses ont disparu et
que de nouvelles apparaissent : il détruit et recrée tout. Le bloc `moved`
déclare le réadressage :

```hcl
moved {
  from = random_pet.bucket[0]
  to   = random_pet.bucket["app"]
}

moved {
  from = random_pet.bucket[1]
  to   = random_pet.bucket["audit"]
}
```

Trois propriétés en font la bonne méthode, préférable à `terraform state mv` :

- il est **versionné** avec le code et revu en revue de code,
- il est **rejoué automatiquement** par toute l'équipe et par la CI,
- il est **déclaratif** : personne n'a à se souvenir d'exécuter une commande.

La documentation officielle recommande de **conserver** les blocs `moved` :
les supprimer est un changement cassant pour ceux qui n'ont pas encore appliqué.

## Lire la preuve dans le plan JSON

Un réadressage réussi se voit dans le plan, et c'est ce que les tests vérifient :

```bash
terraform plan -out=tfplan
terraform show -json tfplan | jq -c '.resource_changes[] | {address, previous_address, actions: .change.actions}'
```

```text
{"address":"random_pet.bucket[\"app\"]","previous_address":"random_pet.bucket[0]","actions":["no-op"]}
{"address":"random_pet.bucket[\"audit\"]","previous_address":"random_pet.bucket[1]","actions":["no-op"]}
```

Deux signatures à connaître :

- `"actions": ["no-op"]` accompagné d'un **`previous_address`** : la ressource a
  changé d'adresse sans être touchée. C'est le résultat recherché.
- `"actions": ["delete", "create"]` : la ressource est **remplacée**. Le
  réadressage a échoué.

## Le splat trompeur sur for_each

Un dernier piège, qui apparaît dans beaucoup de tutoriels, souvent mal décrit. La
syntaxe splat `ressource[*].attribut` est conçue pour les **listes**. Sur une
ressource pilotée par `for_each`, qui est une **map**, elle ne lève pourtant
aucune erreur : elle emballe silencieusement la map dans un tableau à un seul
élément.

```bash
echo 'random_pet.bucket[*]' | terraform console
```

```text
[
  {
    "app" = { "id" = "relaxed-griffon", ... }
    "audit" = { "id" = "enough-boa", ... }
  },
]
```

La map entière devient l'unique élément d'une liste. Du coup, `[*].id` cherche un
attribut `id` sur ce tableau et rend une **liste vide**, sans un mot
d'avertissement. C'est plus dangereux qu'une erreur franche : le plan passe, et
votre output est faux.

La bonne forme est une expression `for` :

```hcl
output "noms" {
  value = { for cle, r in random_pet.bucket : cle => r.id }
}
```

```text
{
  "app" = "relaxed-griffon"
  "audit" = "enough-boa"
}
```

Si vous tenez à une liste plutôt qu'à une map, `values(random_pet.bucket)[*].id`
fonctionne, parce que `values()` transforme d'abord la map en liste.

## À vous de jouer

Vous savez migrer de `count` vers `for_each` sans casser l'existant, et lire la
preuve dans le plan. Le challenge vous attend sur un autre décor : la
configuration livrée est **correcte et déjà appliquée**, rien n'est troué. C'est
son architecture qu'il faut changer, sans détruire.

```bash
dsoxlab run write-code-for-each
dsoxlab check write-code-for-each
dsoxlab hint write-code-for-each
```

Sous-objectif d'examen visé : **2d** (Terraform Authoring and Operations
Professional), les meta-arguments.

Référence : [for_each Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/for-each-terraform/)
