# Les quatre niveaux de validation Terraform

Terraform a **quatre** dispositifs pour valider une configuration. Ils se
ressemblent à l'écrit, mais un seul **n'arrête pas** l'opération. Savoir lequel
mettre où, et lequel bloque, est l'objectif d'examen **2a**. Ce tutoriel les pose
sur un exemple **jetable** de dimensionnement ; le challenge vous les fera
coexister et prouver.

## 1. `validation` : refuser une entrée avant le plan

Dans un bloc `variable`, un bloc `validation` refuse une valeur d'entrée **avant
tout plan**. Depuis Terraform **1.9**, sa `condition` peut référencer **une autre
variable** (validation croisée) :

```hcl
variable "replicas" {
  type = number
  validation {
    condition     = var.replicas <= var.replicas_max
    error_message = "replicas ne peut pas dépasser replicas_max."
  }
}
```

## 2. `precondition` : refuser une hypothèse avant la création

Dans `lifecycle`, une `precondition` vérifie une **hypothèse** au plan, avant que
la ressource soit créée. Attention : sur une ressource en `count = 0`, il n'y a
**aucune instance**, donc la précondition **n'est pas évaluée**.

```hcl
resource "aws_instance" "web" {
  # ...
  lifecycle {
    precondition {
      condition     = var.instance_type != "t2.nano"
      error_message = "t2.nano est trop petit pour ce rôle."
    }
  }
}
```

## 3. `postcondition` : refuser un résultat après la création

Toujours dans `lifecycle`, une `postcondition` vérifie le **résultat** après
création. Elle est la **seule** à disposer de **`self`**, l'objet créé :

```hcl
    postcondition {
      condition     = self.private_ip != ""
      error_message = "L'instance n'a pas reçu d'IP privée."
    }
```

## 4. `check` : surveiller sans bloquer

Un bloc `check` de niveau racine **surveille** un invariant. Contrairement aux
trois précédents, un `assert` en échec **n'arrête pas** l'apply : il produit un
**avertissement**, pas une erreur. C'est fait pour des vérifications de continuité
de service qu'on ne veut pas bloquantes.

```hcl
check "sante_http" {
  data "http" "home" {
    url = "https://${aws_instance.web.public_ip}/"
  }
  assert {
    condition     = data.http.home.status_code == 200
    error_message = "La home ne répond pas 200."
  }
}
```

Un `check` peut contenir un **data source scopé**, comme ici. À connaître : ce
data source est **relu à chaque plan**, donc il apparaît toujours en action
`read` dans le plan. Conséquence : **`terraform plan -detailed-exitcode` rend
`2`** (« des changements »), même sur une configuration convergée. Une CI qui
décide sur ce code croira toujours qu'il reste des changements.

## Lire le verdict des quatre : le tableau `checks`

`terraform show -json` expose un tableau **`checks`** de premier niveau. Chaque
entrée porte un `address.kind` (`var`, `resource`, `output_value`, `check`) et un
`status` (`pass` / `fail`). Un `check` en échec porte son message dans
`instances[].problems[].message`. C'est **la** preuve machine des quatre niveaux,
sans jamais lire une sortie humaine.

Un dernier piège : **`terraform validate` ne joue pas ces conditions**. Il ne
connaît pas les valeurs des variables, donc il rend `valid: true` sur une entrée
que le **plan** refusera. `validate` contrôle la forme, le plan contrôle les
valeurs.

## À vous de jouer

Vous savez que `validation`, `precondition` et `postcondition` **bloquent**, que
le bloc `check` **avertit** seulement, que `postcondition` seule a `self`, que le
data source d'un `check` fait sortir `plan -detailed-exitcode` en 2, et que le
tableau `checks` de `show -json` donne le verdict des quatre. Le challenge vous
fait remplir les quatre niveaux et le prouver.

```bash
dsoxlab run write-code-validation-check-preconditions
dsoxlab check write-code-validation-check-preconditions
dsoxlab hint write-code-validation-check-preconditions
```

Sous-objectif d'examen visé : **2a** (valider la configuration), niveau
Professional.

Référence : [Conditions personnalisées](https://developer.hashicorp.com/terraform/language/expressions/custom-conditions)
