# 🎯 Challenge : écrire la suite qui prouve le module

## 📦 Le point de départ

`challenge/work` fonctionne **hors ligne**, sans aucun provider :

| Fichier | Ce que c'est |
| --- | --- |
| `etiquette/` | le module, **complet**, à ne pas modifier |
| `etiquette/tests/etiquette.tftest.hcl` | le squelette de la suite, quatre `run` en `???` |
| `CIBLE.md` | le contrat du module et les quatre comportements à couvrir |

## ✅ Objectif

Écrire la suite `.tftest.hcl` du module `etiquette`, de sorte que `terraform test`
passe **et** qu'elle tombe si le module change de comportement.

## 📋 Ce qu'il faut obtenir

1. `terraform test`, lancé depuis `etiquette/`, sort en **0**.
2. Le résumé JSON annonce `status: pass`, aucun échec, au moins **quatre** `run`
   réussis.
3. Un `run` couvre le **défaut** : avec le seul `prefixe`, l'étiquette vaut
   `atelier` et sa longueur `7`.
4. Un `run` couvre le **suffixe** : `atelier-nord`.
5. Un `run` couvre les **majuscules** : `ATELIER`.
6. Un `run` couvre le **refus** d'un préfixe de moins de trois caractères, sans
   rien appliquer.
7. La suite est **rejouable** et ne laisse aucun `*.tfstate` dans le répertoire du
   module.

## ⚠️ Le cœur du sujet

Une suite qui n'asserte rien **passe au vert** :

```text
$ terraform test
Success! 4 passed, 0 failed.
```

C'est pourquoi la validation de ce lab ne lit pas votre suite : elle **casse le
module**, un comportement à la fois, dans une copie temporaire, et exige que votre
suite s'en aperçoive. Quatre mutations sont jouées : la `validation` du préfixe
disparaît, le défaut du `suffixe` change, le tiret devient un souligné, le passage
en majuscules est retiré.

Le quatrième comportement, le **refus**, ne s'écrit pas comme les autres : il n'y a
rien à assérer quand rien ne doit être produit. C'est l'échec lui-même qui est
attendu, et il faut **nommer** l'objet censé le produire. Un contournement par
assertion sera repéré : la mutation correspondante doit produire
`Error: Missing expected failure`.

## 🔍 Validation

`dsoxlab check modules-test-module` prouve, par exécution :

- un **témoin** : la suite passe sur le module intact, faute de quoi les mutations
  ne prouveraient rien ;
- **quatre mutations**, chacune devant faire échouer votre suite ;
- le **code de retour** de `terraform test`, et le `test_summary` du flux
  `-json` : `status`, `passed`, `failed`, `errored` ;
- la **rejouabilité** : la suite est lancée deux fois, et le répertoire du module
  ne doit garder aucun state.

Bloqué ? `dsoxlab hint modules-test-module`.
