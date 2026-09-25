# 🎯 Challenge : décider, pour chaque bloc, s'il crée ou s'il lit

## 📦 Le point de départ

`challenge/work` contient `catalogue.txt`, **déjà sur le disque** : Terraform ne
l'a jamais créé.

| Fichier | État |
| --- | --- |
| `catalogue.txt` | fourni, **à ne pas modifier** |
| `versions.tf` | le bloc `required_providers` est vide |
| `main.tf` | quatre blocs dont la **nature** est un `???` |
| `outputs.tf` | deux sorties à écrire |

`terraform init` échoue en l'état : il ne sait pas quels providers installer.

## ✅ Objectif

1. **Déclarer les trois providers** (`local`, `null`, `random`) avec une
   contrainte de version **pessimiste**.
2. **Choisir la nature de chaque bloc** : celui qui lit `catalogue.txt`, et ceux
   qui créent.
3. **Référencer plutôt que recopier** : le fichier écrit dérive de ce que le
   catalogue contient, et le `triggers` du sceau porte **à la fois** la valeur
   tirée au sort et ce qui a été lu.
4. **Deux sorties**, de deux natures différentes.

Après votre `apply`, `terraform plan` ne doit plus rien proposer.

## 🧭 Le mot qui décide de tout

`resource` **crée et gère**. `data` **lit**. Et la référence change avec la
nature :

```hcl
local_file.resume.filename              # une resource
data.local_file.catalogue.content       # une data source
```

Deux conséquences que les tests vérifient :

- **une data source ne crée rien**, donc le `destroy` ne l'emporte pas. Si
  `catalogue.txt` disparaît, c'est qu'un bloc `resource` le gérait ;
- **elle est relue à chaque plan**. Modifier `catalogue.txt` sans toucher un
  seul `.tf` doit faire passer `plan -detailed-exitcode` de 0 à **2**. S'il
  reste à 0, la valeur lue n'irrigue rien.

## ⚠️ Deux valeurs qu'on ne peut pas écrire à la main

`random_pet.empreinte.id` n'existe qu'**après création**. Et le contenu du
catalogue doit venir de la data source, pas d'une copie : sinon il ne suivra pas
quand le fichier changera.

## 🔍 Validation

```bash
dsoxlab check getting-started-providers-resources-data-sources
```

Sept tests. Aucun ne lit vos `.tf` : la preuve centrale est le champ `mode` de
`terraform show -json`, qui vaut `managed` ou `data` sans ambiguïté.

Le dernier joue le `destroy` dans une **copie** du répertoire, pour que le lab
reste rejouable.

Bloqué ? `dsoxlab hint getting-started-providers-resources-data-sources`.
