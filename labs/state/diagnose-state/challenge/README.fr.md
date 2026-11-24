# Réconcilier une dérive et adopter une ressource orpheline

## La situation

**Sous-objectif d'examen visé : 1e.**

Un collègue a bricolé un fichier à la main et a laissé traîner une valeur créée
hors Terraform. Ce lab traite le piège laissé ouvert par le guide : croire que
`plan -detailed-exitcode` détecte la dérive, alors qu'il signale un diff non
vide. Le détecteur de dérive fiable, c'est `plan -refresh-only`.

## Capacité visée

Diagnostiquer une dérive avec un plan refresh-only enregistré, la réconcilier
de façon explicite, puis adopter dans le state une ressource préexistante sans
provoquer son remplacement au prochain apply.

## D'où part l'apprenant

`main.tf` est complet et prêt à appliquer : le bloc `terraform` et la ressource
`local_file.note`, qui écrit `data/note.txt`. Un second fichier, `adoption.tf`,
porte l'adoption à venir, **livrée en commentaire** pour que la configuration
s'applique telle quelle : la ressource `random_string.legacy` avec son bloc
`lifecycle` troué, et le bloc `import` dont `to` et `id` sont des `???`.
Décommenté trop tôt, ce fichier ferait **créer** un jeton aléatoire au lieu
d'adopter celui qui existe.

La fixture `token-herite.txt` porte la chaîne créée hors Terraform, connue d'un
service tiers : personne ne peut la regénérer, il faut l'adopter telle quelle.

Aucun `terraform.tfstate` n'existe au départ. L'énoncé fait construire l'état
de référence (`init` puis `apply`), puis simuler l'incident en écrasant
`data/note.txt` à la main. La dérive est donc réelle, pas préfabriquée.

## L'état à atteindre

1. Un plan refresh-only enregistré puis **converti**, sous `derive-plan.json`,
   qui porte au moins une entrée `resource_drift` visant `local_file.note` et
   dont `resource_changes` est **vide** : signature d'un plan refresh-only, un
   plan ordinaire rangeant la même information **dans les deux** listes. La
   conversion (`terraform show -json derive.tfplan > derive-plan.json`) n'est
   pas cosmétique : un fichier de plan est un **binaire**, illisible par les
   tests comme par une revue.
2. Le state ne décrit plus que ce qui existe réellement :
   `terraform plan -refresh-only -detailed-exitcode` sort en **0**.
3. `data/note.txt` a retrouvé le contenu déclaré dans `main.tf`, et
   `local_file.note` est de nouveau présent dans le state en `mode: managed`.
4. `random_string.legacy` figure dans le state en `mode: managed`, son attribut
   `result` valant **exactement** la chaîne de `token-herite.txt`. Une valeur
   regénérée par un simple apply ne peut pas tomber juste.
5. Aucun remplacement en attente sur la ressource adoptée :
   `terraform plan -detailed-exitcode` sort en **0**. Le `length` déclaré (24,
   la politique de l'équipe pour tout nouveau jeton) ne correspond pas au jeton
   hérité (16 caractères) : sans `lifecycle { ignore_changes = all }`, le plan
   annonce `must be replaced` sous l'avertissement `Warning: this will destroy
   the imported resource`, et l'apply **regénère** la valeur. Les deux codes de
   sortie sont à `0` **en même temps** : le state colle au réel, et le réel
   colle au code.

## Comment on le prouve

Les tests lancent Terraform dans `challenge/work` et ne lisent jamais le `.tf`.

- `derive-plan.json` est relu comme un document de plan : le test exige le champ
  `format_version`, une entrée `resource_drift` visant `local_file.note`, et un
  `resource_changes` **vide**. Un plan ordinaire converti échoue à ce dernier
  point.
- `terraform show -json` : le test parcourt `values.root_module.resources`,
  exige les deux adresses en `mode: managed`, compare
  `random_string.legacy.result` au contenu de `token-herite.txt`, et le contenu
  réel de `data/note.txt` au `content` que le state prête à `local_file.note`.
- `terraform plan -detailed-exitcode` et sa variante `-refresh-only`, lancés
  avec `-input=false`, doivent tous deux rendre `0` ; le test échoue sur `2` en
  distinguant les deux causes dans son message.

## 🎯 Challenge : une dérive à prouver, un jeton hérité à adopter

### 📦 Le point de départ

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

### ✅ Objectif

Prouver une dérive, la réconcilier, puis adopter le jeton hérité **sans que
Terraform le regénère**.

### 📋 Ce qu'il faut obtenir

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

### ⚠️ Le cœur du sujet

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

### 🔍 Validation

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
