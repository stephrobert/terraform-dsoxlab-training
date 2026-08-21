# Contraintes de version et lock file

Une **contrainte de version** encadre ce que Terraform accepte : sa version, celle
des providers, celle des modules. Deux choses piègent, et ce lab les traite : le
**sens des opérateurs** (surtout `~>` et le pin exact), et le fait que le bloc
`terraform` n'accepte que des **littéraux**. Ce tutoriel les montre sur un exemple
**jetable** ; le challenge vous les fait poser sur `local` et `random`.

## Les opérateurs

| Opérateur | Sens |
|---|---|
| `= 1.2.0` | **exactement** cette version ; ne se combine avec aucun autre |
| `>= 1.2.0` | borne **inférieure** |
| `< 2.0.0` | borne **supérieure** (exclut les versions plus récentes) |
| `~> 5.0` | pessimiste : `5.x`, mais **pas** `6.0` |
| `~> 5.0.2` | pessimiste : `5.0.x`, mais **pas** `5.1.0` |

`<` et `<=` bornent vers le **haut**, pas vers le bas : c'est l'inversion la plus
fréquente. Et `= 1.2.0` fixe une version unique, à ne combiner avec rien.

## Le pessimiste ~>

`~> 5.0` autorise toute la série `5.x` (jusqu'à `5.99`) sans jamais atteindre
`6.0`. `~> 5.0.2` est plus strict : il verrouille la mineure `5.0.x`. L'erreur
classique est d'écrire `~> 1.0.0` en croyant autoriser les correctifs, alors que
cela fige la mineure.

```hcl
terraform {
  required_version = ">= 1.15.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}
```

## Le bloc terraform n'accepte que des constantes

Le bloc `terraform` est évalué très tôt : il **ne peut référencer aucun objet
nommé**. Une variable, un local ou une fonction dans `required_version` fait
échouer `init` avec `Error: Variables not allowed`. La contrainte est forcément
un **littéral**.

## Le lock file

`.terraform.lock.hcl` verrouille les versions **des providers** (pas des
modules), et **se committe**. Pour chaque provider, il enregistre la version
retenue, les contraintes considérées, et des **empreintes** sous deux schémas :
`h1:` (préféré, calculé sur le contenu) et `zh:` (hérité). On lit la sélection
réelle avec :

```bash
terraform version -json | jq '.provider_selections'
```

Le lock ne suit **pas** les modules : Terraform y sélectionne toujours la version
la plus récente satisfaisant la contrainte, qui peut donc varier d'une machine à
l'autre.

## À vous de jouer

Vous savez que `~>` borne la série, que `=` épingle une version unique, que le
bloc `terraform` n'accepte qu'un littéral, et que le lock file fige les providers
avec des empreintes `h1:`. Le challenge vous fait contraindre Terraform, épingler
un provider exactement, et en borner un autre en pessimiste, et les tests
lisent la sélection et le lock.

```bash
dsoxlab run write-code-version-constraints
dsoxlab check write-code-version-constraints
dsoxlab hint write-code-version-constraints
```

Sous-objectif d'examen visé : **3a** (contraintes de version, lock file).

Référence : [Les contraintes de version en Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/version-constraints-terraform/)
