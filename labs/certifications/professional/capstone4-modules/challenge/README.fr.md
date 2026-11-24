# Pro · Objectif 4, créer, maintenir et utiliser des modules

## La situation

**Objectif d'examen visé : 4** (4a créer un module, 4b l'utiliser, 4c le
refactorer et le versionner, **4d refactorer une configuration existante en
modules**).

## Capacité visée

Transformer une configuration plate et répétitive en **module réutilisable**,
puis la réorganiser **sans détruire ni recréer** les ressources déjà en place.
C'est là que se joue le niveau Professional : un refactor qui détruit la
production est un refactor raté.

## D'où part l'apprenant

Dans `challenge/work`, une configuration plate qui **duplique trois fois** le
même ensemble de ressources, avec seulement quelques valeurs qui changent. Elle
est **déjà appliquée** : un state existe, les ressources sont créées.

## L'état à atteindre

1. Un module local expose une interface propre : des variables d'entrée typées
   et documentées, des outputs utiles, et **aucune valeur en dur**.
2. La racine appelle ce module **trois fois** (ou une fois avec `for_each`), et
   la duplication a disparu.
3. Le module porte ses **propres exigences de version** : un bloc
   `required_providers` avec une contrainte, et **aucune configuration de
   provider**, celles-ci étant héritées de l'appelant.

   Attention au piège que le lab fait constater : l'argument `version` d'un bloc
   `module` **ne s'applique qu'aux modules de registry**. Sur une source locale,
   Terraform refuse à l'`init` :

   ```text
   Error: Invalid registry module source address
   you also set the argument "version", which applies only to registry modules.
   ```

   Mesuré le 2026-09-25. Versionner un module local passe donc par le dépôt qui
   le porte, pas par cet argument.
4. **Le point décisif** : après le refactor, `terraform plan` annonce **zéro
   changement**. Les ressources ont changé d'adresse dans le state (elles vivent
   désormais sous `module.*`) mais n'ont pas été recréées. Cela suppose de
   déplacer les adresses correctement plutôt que de laisser Terraform détruire
   puis recréer.

## Comment on le prouve

- `terraform state list` montre des adresses préfixées par `module.`, et **plus
  aucune** ressource à l'ancienne adresse racine.
- Les identifiants des ressources dans le state sont **identiques** à ceux
  d'avant le refactor : la preuve qu'elles n'ont pas été recréées.
- `terraform plan -detailed-exitcode` sort en **0** juste après le refactor.
- Un test lit le module et vérifie qu'il n'expose aucune valeur en dur là où une
  variable est attendue.

## 🎯 Challenge : extraire un module sans rien recréer

### 📦 Le point de départ

`challenge/work` contient une configuration **plate**, qui duplique trois fois le
même ensemble, et elle est **déjà appliquée** : un `terraform.tfstate` est là,
les neuf objets existent, les fichiers de `out/` sont sur le disque.

| Service | Replicas |
| --- | --- |
| `api` | 3 |
| `web` | 2 |
| `batch` | 1 |

### ✅ Objectif

1. **Extraire un module local** dans `modules/service/`, avec des variables
   typées et **documentées**, et des outputs utiles.
2. **L'appeler une fois par service**, indexé par le **nom** du service.
3. **Ne rien recréer.** Les neuf identifiants du state de départ doivent se
   retrouver, aux nouvelles adresses.
4. Le module **ne configure aucun provider**, mais garde ses propres
   `required_providers`.

Après votre travail, `terraform plan` ne doit plus rien proposer.

### 🧭 Ce qui décide entre un refactor réussi et un refactor raté

Changer d'adresse n'est pas changer d'objet. Sans `moved`, Terraform voit neuf
adresses disparaître et neuf apparaître : il détruit et recrée tout.

```hcl
moved {
  from = random_pet.api_nom
  to   = module.service["api"].random_pet.nom
}
```

**Un plan vide ne prouve pas que rien n'a été détruit** : une configuration qui
aurait tout recréé converge aussi. Ce sont les **identifiants** qui tranchent, et
c'est ce que les tests comparent.

### ⚠️ Trois pièges, chacun mesuré

**`version` ne s'applique qu'aux modules de registry.** Sur `./modules/service`,
Terraform refuse dès l'`init` : « applies only to registry modules ».

**Un bloc à plusieurs arguments s'écrit en plusieurs lignes.** La forme compacte
`moved { from = X  to = Y }` répond « The argument "to" is required », un message
qui ne parle pas de mise en forme.

**Écrivez avec `path.root`, pas `path.module`.** Sinon les fichiers partent dans
le sous-répertoire du module, et Terraform les recrée.

### 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone4-modules
```

Six tests. Ils lisent le state et le plan JSON, jamais vos `.tf`. La preuve
centrale compare les identifiants d'avant et d'après.

Bloqué ? `dsoxlab hint certifications-professional-capstone4-modules`.
