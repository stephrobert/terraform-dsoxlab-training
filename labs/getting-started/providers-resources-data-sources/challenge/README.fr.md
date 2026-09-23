# 🎯 Challenge : ce que Terraform gère, ce qu'il se contente de lire

## Point de départ

`challenge/work` contient quatre fichiers :

- `catalogue.txt` : **il existe déjà**. Personne ne l'a créé avec Terraform, et
  Terraform ne doit jamais le détruire.
- `versions.tf` : **troué**. Le bloc `required_providers` est vide.
- `main.tf` : **troué**. Le mot-clé du premier bloc, le contenu du résumé, et
  les deux déclencheurs.
- `outputs.tf` : **troué**. Deux sorties.

Il n'y a ni `.terraform/`, ni state, ni fichier de verrouillage.

## ✅ Objectif

1. **Déclarez les trois providers** `local`, `null` et `random` avec leur
   `source` et une contrainte **pessimiste** (`~> x.y`).
2. **Choisissez la bonne nature** pour le bloc qui vise `catalogue.txt`. Il doit
   le lire, pas le posséder.
3. **Faites dériver** le contenu de `resume.txt` de ce que ce bloc a lu, et de
   la référence produite par `random_pet`.
4. **Alimentez le déclencheur** de `null_resource` avec les deux natures à la
   fois.
5. **Exposez deux sorties** : la référence produite, et le nombre de lignes du
   catalogue.

## 🧭 Ce que le lab vous fait constater

- **Le state distingue les deux natures sans ambiguïté.** `"mode": "managed"`
  d'un côté, `"mode": "data"` de l'autre, avec une adresse préfixée par `data.`.
- **La référence suffit à créer la dépendance.** `data.TYPE.NOM.ATTRIBUT` d'un
  côté, `TYPE.NOM.ATTRIBUT` de l'autre : un `depends_on` écrit à la main est
  presque toujours le symptôme d'une référence manquante.
- **Modifiez `catalogue.txt` sans toucher à un seul `.tf`, et le plan bouge.**
  Une source de données est relue à chaque plan. Si le plan reste vide, c'est
  que la valeur lue n'irrigue rien.
- **Après `destroy`, `resume.txt` a disparu et `catalogue.txt` est intact.**
  C'est la démonstration complète : écrivez `resource` au lieu de `data`, et
  Terraform efface un fichier qu'il n'a jamais créé.

## 🔍 Validation

```bash
dsoxlab check getting-started-providers-resources-data-sources
```

Huit tests lisant `terraform show -json`, `output -json`, le fichier de
verrouillage et des codes retour. Les deux tests destructeurs, celui qui modifie
le catalogue et celui qui détruit, travaillent sur une **copie** de votre
travail : un test ne casse pas ce qu'il mesure. Aucun ne lit vos `.tf`.
