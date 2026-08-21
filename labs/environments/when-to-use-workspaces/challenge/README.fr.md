# 🎯 Challenge : arbitrer, découper, rebrancher

## 📦 Le point de départ

`challenge/work` contient quatre répertoires, aucun n'est initialisé.

| Répertoire | Ce que c'est |
| --- | --- |
| `mono/` | la configuration à **arbitrer**. En LECTURE : ne l'appliquez pas |
| `socle/` | racine du socle, ses deux `output` sont troués |
| `app/` | racine de l'application, son bloc `data` est troué |
| `bac-a-sable/` | le cas où les workspaces restent légitimes, `lookup` troué |
| `CIBLE.md` | le critère de décision et l'état à atteindre |

## ✅ Ce qu'il faut obtenir

1. `socle/` appliqué, suivant au moins une ressource, exposant **deux** outputs
   non vides.
2. `app/` appliqué, son état contenant une ressource en `mode: data` de type
   `terraform_remote_state`.
3. Un output de `app/` **reprend à l'identique** la valeur du socle.
4. `socle/` et `app/` gèrent des ressources **disjointes**.
5. Ni `socle/` ni `app/` n'utilise de workspace.
6. `bac-a-sable/` a **deux** workspaces, `dev` et `prod`, appliqués.
7. La taille vaut **2** sous `dev` et **8** sous `prod`.
8. Les **quatre** états sont stables.

## ⚠️ Le cœur du sujet

Lisez `mono/main.tf` avant de coder. Le commentaire en tête dit l'essentiel : la
production est gérée par une **autre équipe**, avec ses propres droits sur le
stockage d'état.

Or un bloc `backend` **ne peut référencer aucune valeur nommée** :

```text
Error: Variables not allowed
```

Le backend est donc le **même** pour tous les workspaces d'un répertoire. Ce qui
demande des droits distincts sur l'**état** ne relève plus des workspaces, et
doit devenir une **configuration** à part.

Ce qui ne varie que par la **taille**, en revanche, reste parfaitement à sa place
dans un workspace : c'est le cas de `bac-a-sable/`.

## 🔍 Validation

`dsoxlab check environments-when-to-use-workspaces` prouve, par exécution :

- que `app/` lit réellement l'**état** du socle, via une entrée `mode: data` ;
- que la valeur **traverse** les deux états : le contrôle rejoue le socle avec
  une autre plage réseau, dans une copie, et exige que `app/` **suive**. Une
  valeur recopiée en dur reste figée et tombe ;
- que les deux racines gèrent des ressources **disjointes** ;
- qu'aucune des deux n'utilise de workspace ;
- que le bac à sable a bien ses deux workspaces, avec la bonne taille de chaque
  côté ;
- que les quatre états ont convergé.

Bloqué ? `dsoxlab hint environments-when-to-use-workspaces`.
