# 🎯 Challenge : réparer, puis laisser la donnée piloter

## 📦 Le point de départ

`challenge/work` contient une configuration qui **ne passe pas `terraform init`**.

| Fichier | État |
| --- | --- |
| `versions.tf` | **fourni**, quatre providers locaux |
| `variables.tf` | **fourni**, trois environnements dans une `map(object)` |
| `main.tf` | **trois erreurs** semées, et des valeurs à compléter |
| `outputs.tf` | trois sorties à écrire |

Les valeurs marquées « À COMPLÉTER » sont syntaxiquement correctes et
**fonctionnellement fausses** : la configuration validera avant de faire ce
qu'on lui demande.

## ⚠️ Commencez par `init`, pas par `validate`

`init` **parse** la configuration. Tant qu'une erreur de structure subsiste,
aucun provider n'est installé, et `validate` répond `Missing required provider`,
ce qui n'a rien à voir avec vos erreurs.

La méthode : **init, corriger ce qu'il refuse, init de nouveau, puis validate**.
Les deux autres erreurs apparaissent alors ensemble, avec leur numéro de ligne.

## ✅ Objectif

1. **Corriger les trois erreurs** : une combinaison de méta-arguments interdite,
   un type incompatible, une variable non déclarée.
2. **Normaliser les noms** par des fonctions HCL : `PreProd_EU` doit devenir
   `lab-preprod-eu`.
3. **Le manifeste** est du JSON sérialisé **par une fonction**, portant `nom`,
   `taille` et `etiquette` (l'identifiant du `random_pet` de cet environnement,
   **référencé**).
4. **Un bloc `dynamic`** qui génère un bloc `source` par option. Un
   environnement sans option n'en produit aucun.
5. **Trois sorties** : une map agrégée indexée par nom normalisé, les secrets
   (sensibles), et le nombre d'archives.

## 🧭 Deux pièges qui décident du reste

**`count` ou `for_each`, et le choix n'est pas neutre.** `count` adresse par
position : retirer l'entrée du milieu décale les suivantes, qui sont détruites
et recréées. `for_each` adresse par clé et ne touche que ce qu'on retire.

**Le filtrage d'un `dynamic` se fait dans son `for_each`.** Un `if` dans le
`content` ne réduit pas le nombre de blocs : à ce stade, le bloc est déjà décidé.

## 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone2-dynamic-config
```

Neuf tests, qui lisent `validate -json`, `show -json` et `output -json`.

Le dernier est celui qui compte : il copie votre répertoire, **ajoute un
quatrième environnement**, applique, et exige que tout suive. Tous les autres
tests passeraient sur une configuration écrite à la main pour ces trois
environnements précis ; celui-là, non.

Bloqué ? `dsoxlab hint certifications-professional-capstone2-dynamic-config`.
