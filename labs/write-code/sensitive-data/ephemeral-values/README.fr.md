# Les valeurs éphémères : le secret qui ne touche pas le state

Une valeur **éphémère** existe **pendant** une opération Terraform, puis
disparaît : elle n'est **jamais écrite** dans le state ni dans le plan. C'est la
seule réponse réelle au problème que `sensitive` ne résout pas, puisque
`sensitive` laisse la valeur en clair dans l'état. Ce tutoriel montre le bloc
`ephemeral`, sa règle d'or, et la fonction `ephemeralasnull()`, sur un exemple
**jetable** de session ; le challenge vous fera le prouver sur un autre cas.

L'éphémère est arrivé en **Terraform 1.10** (variables et outputs éphémères), et
la ressource `ephemeral "random_password"` demande **random >= 3.7**.

## Déclarer une valeur éphémère

Un bloc **`ephemeral`** produit une valeur générée à la volée, jamais persistée.
On la référence par `ephemeral.<TYPE>.<NOM>.<ATTR>` :

```hcl
ephemeral "random_password" "session" {
  length = 24
}
```

`ephemeral.random_password.session.result` est disponible pendant le run, mais
**n'apparaît nulle part dans le state**. Contrairement à un `random_password`
ordinaire, dont le `result` est stocké en clair dans l'état, l'éphémère ne laisse
aucune trace sur le disque.

## La règle d'or : jamais dans un attribut persisté

Une valeur éphémère ne peut aller que dans des **contextes éphémères**. La lui
faire toucher un attribut **persisté** lève une erreur nette :

```hcl
resource "local_file" "fuite" {
  content = ephemeral.random_password.session.result   # interdit
}
```

```text
Error: Invalid use of ephemeral value
```

Les contextes **autorisés** sont : un argument **write-only** d'une ressource, un
autre bloc `ephemeral`, une configuration de **provider**, un **provisioner** (et
sa configuration de connexion), un **local** consommé uniquement en contexte
éphémère, une **variable** `ephemeral = true`, et un **output éphémère de module
enfant**.

## Les deux erreurs du module racine

Au niveau **racine**, un output ne peut pas porter d'éphémère, et cela se
manifeste de **deux** façons distinctes :

- déclarer un output **`ephemeral = true`** à la racine :
  `Ephemeral output not allowed` ;
- exposer dans un output racine **ordinaire** une valeur **dérivée** d'un
  éphémère (même sa longueur) : `Ephemeral value not allowed`.

C'est ce second cas que l'on rencontre en premier, dès qu'on essaie d'afficher un
éphémère « pour voir ».

## ephemeralasnull() : exposer sans fuiter

Comment, alors, exposer quelque chose au root sans casser le run ? La fonction
**`ephemeralasnull()`** rend **`null`** toute valeur éphémère hors contexte
éphémère :

```hcl
output "session_masquee" {
  value = ephemeralasnull(ephemeral.random_password.session.result)
}
```

L'output vaut `null`. Ce n'est pas un affichage du secret, c'est sa **neutre**
mise à l'écart : la valeur éphémère ne franchit pas la frontière du state. Sur
une valeur **non** éphémère, `ephemeralasnull()` renverrait la valeur telle
quelle, ce qui en fait aussi un bon révélateur : un `null` prouve que l'entrée
était bien éphémère.

## Variables et outputs éphémères

Une **variable** peut être `ephemeral = true` : sa valeur alimente le run mais
n'est jamais persistée. Un **output de module enfant** peut l'être aussi, pour
faire remonter un éphémère vers le module appelant sans jamais l'écrire. Le cycle
de vie d'une ressource éphémère se déroule en **open / renew / close** pendant
l'opération, invisible dans l'état.

## À vous de jouer

Vous savez qu'une valeur éphémère ne touche **jamais** le state, qu'elle ne peut
aller que dans un contexte éphémère (sinon `Invalid use of ephemeral value`),
qu'un output racine la refuse (`Ephemeral value not allowed`), et que
`ephemeralasnull()` l'expose en `null`. Le challenge vous fait générer un jeton
éphémère, le garder hors du state, et l'exposer proprement, et les tests le
prouvent dans le JSON.

```bash
dsoxlab run write-code-sensitive-data-ephemeral-values
dsoxlab check write-code-sensitive-data-ephemeral-values
dsoxlab hint write-code-sensitive-data-ephemeral-values
```

Sous-objectif d'examen visé : **2f** (gérer les données sensibles), niveau
Professional.

Référence : [Les valeurs éphémères en Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/gestion-donnees-sensibles/ephemeral-values/)
