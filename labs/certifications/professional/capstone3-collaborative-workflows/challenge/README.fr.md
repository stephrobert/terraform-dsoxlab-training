# Pro · Objectif 3, workflows collaboratifs

## La situation

**Objectif d'examen visé : 3** (3a contraintes de version sur le binaire, les
providers et les modules, 3b remote state, 3c workflow en automation, 3d partage
de données entre configurations et workspaces).

## Capacité visée

Faire **collaborer deux configurations séparées** par un state distant partagé,
en verrouillant les versions et en s'exécutant **sans interaction humaine**,
comme le ferait une CI.

## D'où part l'apprenant

Floci tourne en local et fournit le backend **S3**. Deux stacks indépendantes
existent dans `challenge/work` :

- `reseau/` : produit une infrastructure de base et doit **publier** ses
  identifiants en outputs.
- `application/` : doit **consommer** ces valeurs sans jamais les recopier en
  dur.

Les deux stacks ont un bloc `terraform {}` incomplet : ni backend, ni
`required_version`, ni `required_providers` contraints.

## L'état à atteindre

1. Les deux stacks écrivent leur state dans le **backend S3 sur Floci**, chacune
   sous une clé distincte. Plus aucun `terraform.tfstate` local.
2. `application/` lit les valeurs de `reseau/` via la data source
   `terraform_remote_state`. **Aucune valeur codée en dur** : changer une valeur
   dans `reseau/` doit se propager.
3. Les versions sont contraintes : `required_version` sur le binaire et une
   contrainte de version sur le provider.
4. Tout s'exécute en **mode automation** : `-input=false`, sans prompt, avec un
   plan sauvegardé puis appliqué (`plan -out` puis `apply` du fichier de plan).

## Comment on le prouve

- Le bucket S3 sur Floci contient bien les deux clés de state (interrogé via
  l'AWS CLI pointée sur l'endpoint local).
- Le state de `application/` montre que ses ressources portent des valeurs
  **issues des outputs** de `reseau/` : on change une valeur en amont, on
  re-planifie, et l'aval bouge.
- Un `apply` lancé avec `-input=false` sans aucune variable interactive
  aboutit : la configuration est réellement automatisable.
- Idempotence sur les deux stacks.

## 🎯 Challenge : faire collaborer deux stacks sans rien recopier

### 📦 Le point de départ

`challenge/work` contient deux stacks indépendantes et un `CIBLE.md`.

| Répertoire | Ce qu'il doit faire |
| --- | --- |
| `reseau/` | **publier** un socle : identifiant, plage, passerelle |
| `application/` | **consommer** ces valeurs, sans jamais les recopier |

Chaque stack a son `backend.tfbackend` **fourni et complet**, et un `main.tf`
dont le bloc `terraform {}` est un `???`.

Floci fournit le backend S3, et le bucket `capstone3-etats` existe déjà.

### ✅ Objectif

1. **Contraindre les versions** : `required_version` sur le binaire, et une
   contrainte sur chaque provider.
2. **Envoyer les deux states dans le bucket**, sous deux clés distinctes. Plus
   aucun `terraform.tfstate` local.
3. **Publier le contrat** de `reseau/` : trois outputs, dont la passerelle,
   **calculée** depuis la plage et jamais écrite en dur.
4. **Lire l'état distant** depuis `application/`, et en dériver un
   `raccordement.json`.
5. **Tout exécuter en automation** : `-input=false`, `plan -out` puis `apply` du
   **fichier de plan**.

### 🧭 Trois choses qui décident du reste

**Un bloc `backend` n'accepte aucune valeur nommée.** Ni variable, ni local :
`Error: Variables not allowed`. Le backend est résolu avant toute évaluation
d'expression. D'où le bloc vide et le `-backend-config=backend.tfbackend`.

**Ce que l'amont n'expose pas en `output` est invisible d'en face**, même si la
valeur est dans son state. Les outputs sont le contrat de la stack.

**Un `apply` direct relit la configuration** au moment d'appliquer. Appliquer un
plan enregistré garantit que ce qui a été revu est ce qui part.

### ⚠️ Recopier passerait aujourd'hui, et échouerait demain

Un test rejoue `reseau/` avec une autre plage et exige que l'aval suive. Trois
valeurs recopiées à la main restent figées et tombent.

### 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone3-collaborative-workflows
```

Sept tests, aucun ne lit vos `.tf`. Le backend se prouve par l'absence de state
local **et** la présence des deux clés dans le bucket, interrogé côté Floci.

Bloqué ? `dsoxlab hint certifications-professional-capstone3-collaborative-workflows`.
