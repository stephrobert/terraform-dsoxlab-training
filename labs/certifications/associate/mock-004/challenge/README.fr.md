# 🎯 Challenge : un examen blanc dont les réponses se prouvent

## 📦 Le point de départ

`challenge/work` contient **deux répertoires**, et l'ordre dans lequel vous les
traitez n'est pas indifférent.

| Répertoire | Ce qu'il contient |
| --- | --- |
| `examen/` | `questions.fr.md` (40 questions), `reponses.auto.tfvars` (à remplir), `bareme.tf` et `versions.tf` **fournis, à ne pas modifier** |
| `atelier/` | `versions.tf` et `variables.tf` **fournis**, `main.tf` et `outputs.tf` **troués** |

**Commencez par l'atelier.** Les quatre dernières questions n'ont pas de réponse
avant qu'il soit construit : elles portent sur l'état qu'il produit.

## ✅ Ce qu'il faut obtenir

### Dans `atelier/`

1. **Quatre ressources gérées**, et **un seul** bloc `data`.
2. Le bloc `lifecycle` de `local_file.modele_source` porte **trois** choses : la
   règle qui crée avant de détruire, une `precondition` qui refuse au plan une
   empreinte trop courte, et une `postcondition` qui relit le fichier écrit par
   `self`.
3. La data source lit le fichier **produit** par cette ressource, en référençant
   son attribut.
4. `null_resource.garde` attend la data source alors qu'elle n'utilise **aucune**
   de ses données.
5. Un bloc `check` nommé `modele_lisible`, au niveau **racine**.
6. Deux sorties, dont une **sensible**.

### Dans `examen/`

7. Les **40 réponses** dans `reponses.auto.tfvars`, plus aucun `???`.
8. **Score global d'au moins 80 %**, et **aucun objectif sous 50 %**.

## 🧭 Le format des réponses

| Type | Ce qu'on attend | Exemple |
| --- | --- | --- |
| choix unique | une lettre | `b` |
| vrai / faux | `v` ou `f` | `v` |
| choix multiple | les lettres **triées**, collées | `ac`, jamais `ca` |
| atelier | la valeur relevée, en minuscules | `4` |

La casse et les espaces autour sont ignorés : `B` et ` b ` passent tous les
deux. Une entrée laissée à `???` compte comme une **absence**, et les tests
exigent qu'il n'en reste aucune.

Trois sorties vous aident à progresser :

```bash
cd examen
terraform output corrige              # quelles questions sont fausses
terraform output score_par_objectif   # quel objectif est faible
terraform output sans_reponse         # ce qui reste à remplir
```

## ⚠️ Ce que le barème protège, et ce qu'il ne protège pas

Aucune réponse n'existe en clair dans ce que vous recevez : `bareme.tf` ne porte
que des empreintes `sha256` salées. Cela empêche de **lire** les réponses en
ouvrant un fichier.

Cela n'empêche pas de les **retrouver** : le sel est dans le barème, et une
question à choix unique n'a que quatre réponses possibles. Aucun barème local ne
peut faire mieux, et ce lab préfère le dire plutôt que de laisser croire
l'inverse.

Le vrai garde-fou est ailleurs : les quatre dernières questions portent sur
**votre** atelier, et les tests recalculent leurs réponses depuis **votre** état
avant de les comparer. Répondre sans construire échoue sur l'état ; construire
sans répondre échoue sur le score.

## 🔍 Validation

```bash
dsoxlab check certifications-associate-mock-004
```

Dix tests. Ils lisent `terraform show -json` et `terraform output -json` des deux
répertoires, jamais vos `.tf`. Le dernier exige que les **deux** répertoires
soient stables : un bloc `check` qui interrogerait une donnée relue à chaque plan
ramènerait un code 2 et ferait échouer cette vérification.

Bloqué ? `dsoxlab hint certifications-associate-mock-004`.
