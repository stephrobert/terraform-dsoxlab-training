# 🎯 Challenge : une dérive à prouver, un jeton hérité à adopter

## 📦 Le point de départ

`challenge/work` contient un projet **jamais appliqué**. C'est à vous de
construire l'état de référence, puis de provoquer vous-même l'incident : la
dérive de ce lab est **réelle**, pas préfabriquée.

```bash
terraform init
terraform apply
```

| Fichier | Ce que c'est |
| --- | --- |
| `main.tf` | la configuration, complète, **à ne pas modifier** |
| `adoption.tf` | l'adoption à venir, **en commentaire** et trouée de `???` |
| `token-herite.txt` | un jeton créé hors Terraform, **impossible à regénérer** |

`adoption.tf` est livré en commentaire pour une raison précise : décommenté
**avant** le premier `apply`, il ferait **créer** un jeton aléatoire au lieu
d'adopter celui qui existe déjà.

## ✅ Objectif

Prouver une dérive, la réconcilier, puis adopter le jeton hérité **sans que
Terraform le regénère**.

## 📋 Ce qu'il faut obtenir

1. **Simulez l'incident** : après le premier `apply`, écrasez `data/note.txt` à
   la main, comme le ferait un collègue pressé.
2. Un fichier **`derive-plan.json`** qui prouve la dérive : il porte une entrée
   `resource_drift` visant `local_file.note`, et son `resource_changes` est
   **vide**. Un fichier de plan étant binaire, il s'obtient en deux temps,
   `terraform plan -refresh-only -out=...` puis `terraform show -json ... > ...`.
3. `terraform plan -refresh-only -detailed-exitcode` sort en **0** : le state
   décrit de nouveau ce qui existe réellement.
4. `data/note.txt` a retrouvé le contenu déclaré dans `main.tf`.
5. `random_string.legacy` figure dans le state, son attribut `result` valant
   **exactement** la chaîne de `token-herite.txt`.
6. `terraform plan -detailed-exitcode` sort en **0**. Les deux codes valent donc
   **0 en même temps**.

## ⚠️ Le cœur du sujet

Deux pièges, indépendants l'un de l'autre.

**Le premier tient au diagnostic.** Un plan ordinaire range la dérive **à la
fois** dans `resource_drift` et dans `resource_changes` ; seul
`plan -refresh-only` laisse `resource_changes` vide. C'est cette absence que le
test exige, et elle prouve que vous avez employé le bon outil.

**Le second tient à l'adoption.** La politique de l'équipe impose `length = 24`
pour tout nouveau jeton, et le jeton hérité est plus court. Sans garde-fou,
Terraform ne se contente pas d'adopter :

```text
  # random_string.legacy must be replaced
  # (imported from "...")
  # Warning: this will destroy the imported resource
```

Appliqué sans lire, ce plan **regénère** le jeton, et le plan suivant annonce
paisiblement `No changes`. La perte est alors invisible. **Lisez le plan avant
d'appliquer.**

## 🔍 Validation

`dsoxlab check state-diagnose-state` prouve, par exécution :

- `derive-plan.json` est bien un document de plan **refresh-only** portant la
  dérive de `local_file.note` ;
- les deux `-detailed-exitcode` rendent **0**, ce qui se lit comme deux
  affirmations distinctes : le state colle au réel, et le réel colle au code ;
- `data/note.txt` porte le contenu que le state lui prête ;
- le jeton du state est **identique** à celui de `token-herite.txt` : une valeur
  regénérée ne peut pas tomber juste ;
- le state porte exactement les deux adresses attendues.

Aucun test n'ouvre vos fichiers `.tf`.

Bloqué ? `dsoxlab hint state-diagnose-state`.
