# Les fonctions définies par les providers

Depuis **Terraform 1.8**, un provider n'apporte plus seulement des ressources et
des data sources : il peut aussi exposer ses propres **fonctions**. On les appelle
par un namespace dédié, **`provider::<nom_local>::<fonction>`**, qui les distingue
sans ambiguïté des fonctions intégrées du langage (`max`, `jsonencode`…). Ce
tutoriel montre le mécanisme sur le provider **intégré `terraform`**, utilisable
**hors ligne** ; le challenge vous le fera pratiquer sur deux autres de ses
fonctions.

## Déclarer le provider, même intégré

Une fonction de provider n'est disponible que si le provider est **déclaré** dans
`required_providers`, y compris le provider intégré `terraform` :

```hcl
terraform {
  required_providers {
    terraform = {
      source = "terraform.io/builtin/terraform"
    }
  }
}
```

Sans cette déclaration, l'appel échoue avec **`Unknown provider function`**, qui
rappelle justement d'ajouter le provider à `required_providers`. Le nom local
choisi ici (`terraform`) est celui qui apparaît dans le namespace d'appel.

## Appeler une fonction du provider

Le provider intégré `terraform` expose trois fonctions, toutes hors ligne. La
plus simple à observer est **`encode_expr`**, qui sérialise n'importe quelle
valeur en **syntaxe d'expression Terraform** :

```hcl
output "expr" {
  value = provider::terraform::encode_expr([1, "deux", true, null])
}
```

L'output vaut la chaîne `[1, "deux", true, null]`. C'est utile pour **générer**
du code Terraform ou un fragment de configuration à partir de données calculées,
sans assembler la chaîne à la main.

## Ce que le namespace garantit

Le préfixe `provider::` n'est pas décoratif : il **lève toute ambiguïté** entre
une fonction du langage et une fonction de provider, et rend explicite **de quel
provider** vient la fonction. Deux providers peuvent exposer une fonction du même
nom sans collision, puisque le nom local les sépare
(`provider::terraform::…` contre `provider::autre::…`).

Une fonction de provider est une **fonction pure** : elle prend des arguments,
rend une valeur, ne touche à rien. Elle s'évalue au plan, ne crée aucune
ressource, et n'apparaît pas dans le state.

## Une fonction peut exiger une version précise du provider

Une fonction n'existe qu'à partir de la **version du provider** qui l'a
introduite. Une contrainte trop basse dans `required_providers` **passe l'`init`**
mais fait échouer l'**appel** : la fonction n'est tout simplement pas dans le
plugin installé. Poser la bonne borne de version fait donc partie de l'exercice,
au même titre que l'appel lui-même.

Deux commandes prouvent d'où vient une fonction, sans ambiguïté :

- **`terraform providers schema -json`** décrit les fonctions de chaque provider,
  dans `provider_schemas[<adresse>].functions` ;
- **`terraform metadata functions -json`** ne liste **que** les ~238 fonctions du
  langage. Une fonction absente d'ici mais présente dans un schéma de provider
  vient du plugin.

## À vous de jouer

Vous savez qu'une fonction de provider s'appelle par
`provider::<nom_local>::<fonction>`, que le provider doit être déclaré dans
`required_providers` (même le provider intégré, ici sous le nom `tfcore`), qu'une
fonction peut exiger une version minimale du provider, et que ces fonctions sont
pures. Le challenge vous fait **sérialiser** un objet en tfvars, faire
**l'inverse**, produire une **syntaxe d'expression**, et tester l'existence d'un
répertoire avec une fonction d'un provider tiers. Les tests le prouvent sur les
sorties JSON.

```bash
dsoxlab run write-code-provider-defined-functions
dsoxlab check write-code-provider-defined-functions
dsoxlab hint write-code-provider-defined-functions
```

Sous-objectif d'examen visé : **2c** (fonctions), appui **5a** (providers),
niveau Professional.

Référence : [Provider-defined functions](https://developer.hashicorp.com/terraform/language/functions)
