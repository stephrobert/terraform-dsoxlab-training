# 🎯 Challenge : deux environnements réellement isolés

## 📦 Le point de départ

`challenge/work` fonctionne **hors ligne**, backend `local` :

| Dossier | Ce que c'est |
| --- | --- |
| `modules/plaque/` | le module partagé, **complet** |
| `envs/dev/` | racine, `backend "local" {}` vide, appel de module troué |
| `envs/prod/` | la même chose, à d'autres valeurs |
| `CIBLE.md` | les valeurs par environnement et la commande d'initialisation |

## ✅ Objectif

Donner à chaque environnement son **état** propre, sans dupliquer le module ni le
bloc de backend.

## 📋 Ce qu'il faut obtenir

1. Les deux racines appellent le module partagé par un chemin **relatif**.
2. `dev` produit **une** plaque, `prod` en produit **trois**.
3. `etats/dev.tfstate` et `etats/prod.tfstate` existent, **hors** des racines.
4. Le bloc `backend` reste **vide** : le chemin passe par `-backend-config`.
5. Les deux environnements convergent.

## ⚠️ Le cœur du sujet

Un bloc `backend` n'accepte **aucune** valeur nommée :

```text
Error: Variables not allowed

Variables may not be used here.
```

D'où la **configuration partielle** : le bloc reste vide, identique partout, et les
arguments manquants arrivent à l'initialisation.

```bash
terraform init -backend-config=<votre-fichier>.hcl
```

Et l'argument officiel contre les workspaces pour ce cas n'est pas l'ergonomie :
« CLI workspaces within a working directory use the **same backend** », donc un
seul jeu de credentials pour tous les environnements.

## 🔍 Validation

`dsoxlab check environments-separate-environments` prouve, par exécution :

- la configuration de backend **enregistrée** par chaque racine, dans
  `.terraform/terraform.tfstate` ;
- le compte de ressources et les sorties de chaque état ;
- le partage du **même** module, lu dans les deux `modules.json` ;
- **l'isolation** : un `destroy` réel dans `dev`, joué sur une copie, doit laisser
  l'état de `prod` intact.

Bloqué ? `dsoxlab hint environments-separate-environments`.
