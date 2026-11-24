# Prouver un module par sa propre suite de tests

## La situation

**Sous-objectif d'examen visé : 4d (tester un module).**

Une assertion qui passe ne prouve rien : ce lab exige une suite qui **échoue
quand le module se casse**. `terraform test` s'exécute contre la configuration du
**répertoire courant**, donc une suite posée dans `<module>/tests/` teste le module
lui-même, sans configuration racine enveloppante.

## Capacité visée

Écrire la suite `.tftest.hcl` d'un module de façon à couvrir son comportement par
**défaut**, chacune de ses **options**, et son **refus** d'une entrée invalide,
puis prouver que cette suite détecte réellement une régression.

## D'où part l'apprenant

`challenge/work` fonctionne **hors ligne**, sans aucun provider :

- `etiquette/` : le module, **complet** et à ne pas modifier. Une variable requise
  `prefixe` avec une `validation` de longueur, deux variables facultatives
  `suffixe` et `majuscules`, les sorties `etiquette` et `longueur`.
- `etiquette/tests/etiquette.tftest.hcl` : le squelette de la suite, quatre `run`
  dont les noms, les conditions et les messages sont des `???`.
- `CIBLE.md` : le contrat du module et les quatre comportements à couvrir, sans
  donner la syntaxe.

## L'état à atteindre

1. La suite vit dans `etiquette/tests/` et porte l'extension `.tftest.hcl`.
2. `terraform test` sort en **0** depuis le répertoire du module.
3. Le résumé JSON annonce `status: pass`, aucun échec, et au moins **quatre**
   `run` réussis.
4. Un `run` couvre le **défaut** : avec le seul `prefixe`, l'étiquette vaut
   `atelier` et sa longueur `7`.
5. Un `run` couvre le **suffixe** : `atelier-nord`, tiret compris.
6. Un `run` couvre les **majuscules** : `ATELIER`.
7. Un `run` couvre le **refus** d'un préfixe trop court, sans rien appliquer, en
   déclarant l'objet attendu en échec.
8. La suite est **rejouable** et ne laisse aucun state derrière elle.

## Comment on le prouve

Le livrable étant une suite de tests, la lire ne prouverait rien : une suite sans
assertion passe au vert et sort en 0. Les tests **mutent** donc le module dans un
répertoire temporaire, un comportement à la fois, et exigent que la suite de
l'apprenant s'en aperçoive.

- Un **témoin** vérifie d'abord que la suite passe sur le module **intact**. Sans
  lui, une suite absente ferait échouer tous les mutants, et les tests de mutation
  passeraient sans qu'une seule assertion ait été écrite.
- **Quatre mutations** : retrait de la `validation`, défaut de `suffixe` changé,
  séparateur `-` remplacé par `_`, `upper()` retiré. Chacune doit faire échouer la
  suite.
- La mutation de la `validation` doit en outre produire
  `Error: Missing expected failure`, ce qui prouve l'emploi d'`expect_failures`
  plutôt qu'une assertion de contournement.
- Le flux `terraform test -json` fournit le résumé machine, `test_summary`, avec
  `status`, `passed`, `failed` et `errored`.
- La suite est lancée **deux fois** de suite, et le répertoire du module ne doit
  contenir aucun `*.tfstate` après coup.

Un `challenge/work` nu rend 1 test sur 9. Une suite de quatre `run` **sans aucune
assertion** passe `terraform test` mais tombe sur 5 tests : c'est exactement le cas
que les mutations existent pour attraper.

## 🎯 Challenge : écrire la suite qui prouve le module

### 📦 Le point de départ

`challenge/work` fonctionne **hors ligne**, sans aucun provider :

| Fichier | Ce que c'est |
| --- | --- |
| `etiquette/` | le module, **complet**, à ne pas modifier |
| `etiquette/tests/etiquette.tftest.hcl` | le squelette de la suite, quatre `run` en `???` |
| `CIBLE.md` | le contrat du module et les quatre comportements à couvrir |

### ✅ Objectif

Écrire la suite `.tftest.hcl` du module `etiquette`, de sorte que `terraform test`
passe **et** qu'elle tombe si le module change de comportement.

### 📋 Ce qu'il faut obtenir

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

### ⚠️ Le cœur du sujet

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

### 🔍 Validation

`dsoxlab check modules-test-module` prouve, par exécution :

- un **témoin** : la suite passe sur le module intact, faute de quoi les mutations
  ne prouveraient rien ;
- **quatre mutations**, chacune devant faire échouer votre suite ;
- le **code de retour** de `terraform test`, et le `test_summary` du flux
  `-json` : `status`, `passed`, `failed`, `errored` ;
- la **rejouabilité** : la suite est lancée deux fois, et le répertoire du module
  ne doit garder aucun state.

Bloqué ? `dsoxlab hint modules-test-module`.
