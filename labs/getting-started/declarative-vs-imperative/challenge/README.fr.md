# 🎯 Challenge : prouver l'idempotence là où le script diverge

## Point de départ

`challenge/work` contient quatre fichiers :

- `imperatif.sh` : **fourni, à lire, pas à corriger**. Il fabrique un répertoire
  de sortie, y écrit un rapport et y inscrit un identifiant tiré à chaque appel.
  Rejouez-le deux fois et comparez : l'identifiant change, et le rapport
  s'allonge.
- `versions.tf` : **complet**. Il épingle `local`, `null` et `random`.
- `main.tf` : **troué**. Trois ressources, dont les arguments qui décident du
  caractère stable ou non des valeurs générées.
- `outputs.tf` : **troué**. Deux sorties.

Il n'y a ni `.terraform/`, ni state, ni fichier de verrouillage.

## ✅ Objectif

Obtenez en Terraform le même résultat que le script, puis prouvez ce qui les
sépare.

1. **`random_string.identifiant`** : huit caractères, ni majuscules ni
   caractères spéciaux, et un `keepers` qui le rende **stable**.
2. **`local_file.rapport`** : son contenu est **construit** à partir de
   l'identifiant, et le fichier est **remplacé**, jamais empilé.
3. **`null_resource.empreinte`** : son déclencheur dépend de l'identifiant.
4. **Les deux sorties** : l'identifiant, et le chemin du rapport.

Puis, sans modifier votre code : supprimez le rapport à la main, constatez la
dérive, et laissez Terraform réparer.

## 🧭 Ce que le lab vous fait constater

- **Deux passages du script donnent deux identifiants.** Deux `apply` du même
  code n'en donnent qu'un : la valeur est mémorisée dans le state.
- **Le rapport impératif s'allonge, le rapport déclaratif est remplacé.** L'un
  décrit un historique, l'autre un état.
- **Après suppression du rapport, le plan annonce une seule création.**
  L'identifiant n'est pas retiré, et la `null_resource` n'est pas remplacée : la
  dérive se répare là où elle a eu lieu.
- **L'identifiant survit à la réparation.** C'est `keepers` qui le garantit,
  et rien d'autre.

## 🔍 Validation

```bash
dsoxlab check getting-started-declarative-vs-imperative
```

Huit tests lisant `terraform show -json`, `output -json`, un plan enregistré
avec `-out` et relu en JSON, et des codes retour. Le dernier compare les deux
approches sur le même geste : le script rejoué diverge, la configuration rejouée
ne bouge plus. Aucun ne lit vos `.tf`.
