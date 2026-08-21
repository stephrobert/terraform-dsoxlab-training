# Scénario : prouver un module par sa propre suite de tests

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
