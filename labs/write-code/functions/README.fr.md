# Composer des valeurs avec les fonctions HCL

**Sous-objectif d'examen visé : 2c**, calculer et interpoler des données avec les
fonctions HCL.

Les fonctions passent pour la partie facile de l'examen, jusqu'au jour où un
index hors bornes, une clé absente ou un template mal échappé fait échouer un
plan. Ce lab enchaîne ces pièges, puis ajoute ce que presque aucun tutoriel ne
traite : les fonctions exposées par un provider.

Guide de référence :
[Les fonctions Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/fonctions-terraform/)

## Prérequis

- `terraform` sur le PATH, en version **1.8 ou plus récente** (les fonctions de
  provider n'existent pas avant).
- Un accès réseau pour le premier `terraform init` seulement, le temps de
  télécharger le provider `hashicorp/local`.

Vérifiez votre version :

```bash
terraform version
```

## 1. La console, avant d'écrire quoi que ce soit

`terraform console` fonctionne **dans un répertoire vide, sans `terraform init`**.
C'est le réflexe à prendre : on teste l'expression, puis on l'écrit.

```bash
echo 'upper("lab")' | terraform console
```

```
"LAB"
```

L'initialisation ne devient nécessaire que si l'expression touche un provider,
un module ou une data source. Une fonction de provider en fait partie.

## 2. Découper, dédupliquer, et pourquoi ça compte

Une chaîne CSV arrive souvent d'une variable de CI. `split()` la transforme en
liste :

```bash
echo 'split(",", "prod,dev,prod,staging")' | terraform console
```

```
tolist([
  "prod",
  "dev",
  "prod",
  "staging",
])
```

Cette liste contient un doublon. La passer telle quelle à un `for_each` échoue,
parce que `for_each` exige un **set** ou une **map**. `toset()` fait la
conversion et supprime le doublon au passage :

```bash
echo 'toset(split(",", "prod,dev,prod,staging"))' | terraform console
```

```
toset([
  "dev",
  "prod",
  "staging",
])
```

L'enjeu n'est pas cosmétique. Avec un set, chaque instance est adressée dans le
state par **sa valeur** (`["dev"]`), et non par une position (`[0]`). Insérer un
environnement plus tard ne décale donc rien.

## 3. element : le rebouclage modulo

C'est le premier piège. `element()` ne se comporte pas comme un accès par index
classique.

```bash
echo 'element(["dev","staging","prod"], 5)' | terraform console
```

```
"prod"
```

L'index 5 sur trois éléments donne `5 % 3 = 2`, donc le troisième élément.
**`element()` ne retombe pas sur le premier élément**, elle calcule un modulo.
Deux comportements à retenir en plus : `element(liste, -1)` rend le dernier
élément, et `element([], 0)` lève une erreur.

Pour un accès strict qui échoue hors bornes, utilisez `liste[index]`.

## 4. lookup : la valeur de repli n'est pas optionnelle

Deuxième piège. Beaucoup de tutoriels affirment que `lookup()` rend `null` quand
la clé est absente. C'est faux :

```bash
echo 'lookup({dev = "small"}, "qa")' | terraform console
```

```
Error: Invalid function argument
  the given object has no attribute "qa"
```

La forme à deux arguments est de surcroît **dépréciée depuis Terraform 0.7**.
Passez toujours le troisième argument :

```bash
echo 'lookup({dev = "small"}, "qa", "small")' | terraform console
```

```
"small"
```

## 5. merge : la dernière map gagne

```bash
echo 'merge({projet = "demo"}, {env = "qa"})' | terraform console
```

```
{
  "env" = "qa"
  "projet" = "demo"
}
```

En cas de clé présente des deux côtés, c'est la **dernière** qui l'emporte. C'est
ce qui permet de définir un socle de tags communs et d'y surcharger une valeur au
dernier moment.

## 6. ceil : arrondir dans le bon sens

Terraform ne connaît qu'un seul type `number`, qui accepte les décimales. Une
division rend donc un flottant :

```bash
echo '1536 / 1024' | terraform console        # 1.5
echo 'ceil(1536 / 1024)' | terraform console
```

```
2
```

Pour un dimensionnement de mémoire ou de disque, `floor()` produirait une
ressource trop petite. `ceil()` garantit qu'elle reste suffisante.

## 7. templatefile : n'échappez que `${`

Troisième piège, et le plus coûteux. Dans un template, **seule la séquence `${`
doit être échappée en `$${`**. Un `$` littéral suivi d'autre chose passe tel quel.

Le fichier `node.yaml.tftpl` du lab contient les quatre cas :

```
hostname: ${hostname}
litteral: $${AUTRE}
script: |
  echo "home=$HOME"
  echo "date=$(date)"
```

Après rendu, `${hostname}` est substitué, `$${AUTRE}` devient le texte
`${AUTRE}`, et `$HOME` comme `$(date)` restent intacts pour que bash les
interprète à l'exécution.

Échapper systématiquement tous les `$` en `$$`, comme le recommandent beaucoup de
tutoriels, **corrompt le script** : bash interprète `$$` comme le PID du
processus, et `$$HOME` s'affiche en `786103HOME`.

## 8. Les fonctions de provider

On ne peut pas définir ses propres fonctions en HCL, mais un provider peut en
exposer. Depuis **Terraform 1.8**, elles s'appellent ainsi :

```
provider::<nom_local>::<fonction>(...)
```

Le point qui piège : `<nom_local>` est le nom déclaré dans `required_providers`,
pas le nom du provider. Le provider **intégré** `terraform` permet de tester sans
rien télécharger :

```hcl
terraform {
  required_providers {
    terraform = { source = "terraform.io/builtin/terraform" }
  }
}
```

Il expose `encode_tfvars`, `decode_tfvars` et `encode_expr` :

```hcl
provider::terraform::encode_tfvars({ env = "qa", gib = 2 })
# rend la chaine : env = "qa"\ngib = 2\n
```

Après avoir ajouté un provider dans `required_providers`, il faut **relancer
`terraform init`**, sinon l'appel échoue sur `Unknown provider`.

## 9. Quand une fonction est-elle évaluée ?

Toutes les erreurs de fonctions ne tombent pas au plan. Une fonction appliquée à
une valeur **inconnue au moment du plan**, parce qu'elle vient d'une ressource
non encore créée, n'est évaluée qu'à l'`apply`. L'erreur survient alors **après**
que des ressources ont été créées, et il faut ensuite réconcilier l'état partiel.

C'est la raison pour laquelle une validation explicite vaut mieux qu'une fonction
qui échouera peut-être trop tard.

## À vous de jouer

Le challenge vous attend dans `challenge/README.fr.md`. La configuration fournie
ne se valide pas : sept `locals` et deux attributs de ressource sont à compléter.

```bash
dsoxlab run write-code-functions
dsoxlab check write-code-functions
```

En cas de blocage, trois indices de coût croissant sont disponibles :

```bash
dsoxlab hint write-code-functions
```
