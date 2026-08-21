# Le style guide : ce que la CI vérifie, et pourquoi

Un style guide ne se relit pas, il se **fait rejeter par une CI**. Les noms de
fichiers ne changent rien au comportement de Terraform, donc les vérifier ne
prouve rien ; ce qui prouve, c'est le code retour de `terraform fmt -check` et le
JSON de `terraform validate`. Ce tutoriel parcourt les règles officielles sur
des exemples **génériques** ; le challenge vous fera reprendre une configuration
dégradée et la rendre conforme.

## Le nommage des fichiers, et ses exceptions

Terraform **concatène tous les `.tf`** d'un dossier : la découpe est une
convention de lisibilité, sans effet technique... à deux exceptions près. Le
style guide officiel recommande :

- **`terraform.tf`** : le bloc `terraform` (`required_version`,
  `required_providers`). Attention, le nom officiel est `terraform.tf`, pas
  `versions.tf`.
- **`providers.tf`** : tous les blocs `provider`.
- **`variables.tf`** : toutes les variables, **en ordre alphabétique**.
- **`main.tf`** : ressources et data sources.
- **`outputs.tf`** : tous les outputs, **en ordre alphabétique**.

Les deux exceptions où le nom **a** un effet : les fichiers `*_override.tf` (et
`override.tf`) sont chargés **en dernier** et fusionnés par-dessus le reste ; et
un dépôt de module publié doit s'appeler `terraform-<PROVIDER>-<NOM>`.

## Nommer une ressource

Une ressource se nomme avec un **nom descriptif en snake_case**, sans répéter le
type que l'adresse porte déjà :

```hcl
# bien : l'adresse est random_pet.serveur
resource "random_pet" "serveur" {}

# mal : camelCase, et le nom repete le type
resource "random_pet" "randomPetServeur" {}
```

Le nom `this` pour la ressource unique d'un module est une convention
**communautaire** répandue, mais le style guide officiel ne la mentionne pas :
il demande seulement un nom descriptif.

## L'ordre à l'intérieur d'un fichier, et d'une ressource

Deux ordres officiels sont souvent inversés. D'abord, **les ressources
dépendantes se déclarent APRÈS celles qu'elles référencent** (« let your code
build on itself »), et **une data source avant la ressource qui la consomme**.

Ensuite, à l'intérieur d'un bloc `resource`, l'ordre des paramètres est :

1. `count` ou `for_each` (si présent) ;
2. les arguments non-bloc de la ressource ;
3. les arguments de type bloc ;
4. un bloc `lifecycle` (si besoin) ;
5. **`depends_on` en DERNIER** (si besoin).

Beaucoup de guides placent `depends_on` en tête avec les autres meta-arguments :
c'est l'inverse de la règle officielle.

## Les commentaires : # est idiomatique

HCL accepte `#`, `//` et `/* */`, mais la doc tranche : **seul `#` est
idiomatique**, en une ligne comme en plusieurs. « The `//` and `/* */` comment
syntaxes are not considered idiomatic. » Les deux autres ne survivent que par
compatibilité ascendante.

## Typer les variables ET les outputs

Depuis Terraform 1.15, le style guide demande un **`type`** et une
**`description`** sur chaque **output**, comme pour les variables. Le type n'est
pas cosmétique : il documente le contrat et corrige les valeurs. Un output
`type = number` dont la valeur vient d'un `terraform.tfvars` qui l'écrit `"3"`
(entre guillemets) ressort en **nombre** :

```hcl
output "nombre_noeuds" {
  type        = number
  description = "Nombre de noeuds."
  value       = var.nombre_noeuds
}
```

L'ordre officiel des paramètres est `type`, `description`, `default`,
`sensitive`, `validation` pour une variable ; `type`, `description`, `value`,
`sensitive` pour un output.

## Formater et valider, avant la CI

Deux commandes, deux rôles distincts :

- **`terraform fmt`** normalise l'indentation, aligne les `=`, espace les maps
  inline. `terraform fmt -check` sort en **code 3** (pas 1) quand un fichier
  n'est pas formaté.
- **`terraform validate`** vérifie la cohérence interne et les **types**, mais
  **ne** valide **pas** les valeurs auprès du provider et **n'**évalue **pas**
  le state.

Le linting va plus loin : Terraform n'a pas de linter intégré, la doc recommande
**TFLint**. Et le bon endroit pour lancer `fmt` et `validate` est un **hook de
pré-commit** Git, là où l'erreur se corrige le moins cher, avant même la CI.

## Le .gitignore : le state dehors, le lock dedans

C'est la seule règle du style guide dont l'oubli a des conséquences de sécurité
immédiates. On **n'committe jamais** : le répertoire `.terraform/`, les fichiers
`terraform.tfstate*`, `.terraform.tfstate.lock.info`, les plans sauvegardés par
`-out`, et tout `.tfvars` sensible. On **committe** en revanche
**`.terraform.lock.hcl`**, le fichier de verrouillage des versions de providers.

<Aside type="caution" title="Le piège du .terraform*">
Ignorer le répertoire par `.terraform/` (avec le slash) est correct. Écrire
`.terraform*` (avec l'étoile) ignore **aussi** `.terraform.lock.hcl`, qui doit
pourtant être committé. Le slash final restreint le motif au répertoire.
</Aside>

## À vous de jouer

Vous savez que le bloc `terraform` va dans `terraform.tf`, que les ressources se
nomment en snake_case sans répéter le type, que `depends_on` va en dernier, que
`#` est le seul commentaire idiomatique, que les outputs se typent depuis la
1.15, et qu'un `.gitignore` sort le state mais garde le lock. Le challenge vous
fait reprendre une configuration dégradée, et les tests prouvent sa conformité
par `fmt -check`, `validate` et le JSON.

```bash
dsoxlab run write-code-style-guide
dsoxlab check write-code-style-guide
dsoxlab hint write-code-style-guide
```

Sous-objectifs d'examen visés : **2a** (valider la configuration) et **2e**
(typage des variables et outputs).

Référence : [Le style guide Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/ecrire-code/style-guide-terraform/)
