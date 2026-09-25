# 🎯 Challenge : faire collaborer deux stacks sans rien recopier

## 📦 Le point de départ

`challenge/work` contient deux stacks indépendantes et un `CIBLE.md`.

| Répertoire | Ce qu'il doit faire |
| --- | --- |
| `reseau/` | **publier** un socle : identifiant, plage, passerelle |
| `application/` | **consommer** ces valeurs, sans jamais les recopier |

Chaque stack a son `backend.tfbackend` **fourni et complet**, et un `main.tf`
dont le bloc `terraform {}` est un `???`.

Floci fournit le backend S3, et le bucket `capstone3-etats` existe déjà.

## ✅ Objectif

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

## 🧭 Trois choses qui décident du reste

**Un bloc `backend` n'accepte aucune valeur nommée.** Ni variable, ni local :
`Error: Variables not allowed`. Le backend est résolu avant toute évaluation
d'expression. D'où le bloc vide et le `-backend-config=backend.tfbackend`.

**Ce que l'amont n'expose pas en `output` est invisible d'en face**, même si la
valeur est dans son state. Les outputs sont le contrat de la stack.

**Un `apply` direct relit la configuration** au moment d'appliquer. Appliquer un
plan enregistré garantit que ce qui a été revu est ce qui part.

## ⚠️ Recopier passerait aujourd'hui, et échouerait demain

Un test rejoue `reseau/` avec une autre plage et exige que l'aval suive. Trois
valeurs recopiées à la main restent figées et tombent.

## 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone3-collaborative-workflows
```

Sept tests, aucun ne lit vos `.tf`. Le backend se prouve par l'absence de state
local **et** la présence des deux clés dans le bucket, interrogé côté Floci.

Bloqué ? `dsoxlab hint certifications-professional-capstone3-collaborative-workflows`.
