# 🎯 Challenge : extraire un module sans rien recréer

## 📦 Le point de départ

`challenge/work` contient une configuration **plate**, qui duplique trois fois le
même ensemble, et elle est **déjà appliquée** : un `terraform.tfstate` est là,
les neuf objets existent, les fichiers de `out/` sont sur le disque.

| Service | Replicas |
| --- | --- |
| `api` | 3 |
| `web` | 2 |
| `batch` | 1 |

## ✅ Objectif

1. **Extraire un module local** dans `modules/service/`, avec des variables
   typées et **documentées**, et des outputs utiles.
2. **L'appeler une fois par service**, indexé par le **nom** du service.
3. **Ne rien recréer.** Les neuf identifiants du state de départ doivent se
   retrouver, aux nouvelles adresses.
4. Le module **ne configure aucun provider**, mais garde ses propres
   `required_providers`.

Après votre travail, `terraform plan` ne doit plus rien proposer.

## 🧭 Ce qui décide entre un refactor réussi et un refactor raté

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

## ⚠️ Trois pièges, chacun mesuré

**`version` ne s'applique qu'aux modules de registry.** Sur `./modules/service`,
Terraform refuse dès l'`init` : « applies only to registry modules ».

**Un bloc à plusieurs arguments s'écrit en plusieurs lignes.** La forme compacte
`moved { from = X  to = Y }` répond « The argument "to" is required », un message
qui ne parle pas de mise en forme.

**Écrivez avec `path.root`, pas `path.module`.** Sinon les fichiers partent dans
le sous-répertoire du module, et Terraform les recrée.

## 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone4-modules
```

Six tests. Ils lisent le state et le plan JSON, jamais vos `.tf`. La preuve
centrale compare les identifiants d'avant et d'après.

Bloqué ? `dsoxlab hint certifications-professional-capstone4-modules`.
