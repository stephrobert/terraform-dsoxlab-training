# Ce que la suite de tests doit prouver

Le module `etiquette/` est **complet** et ne doit pas être modifié. Ce qui manque,
c'est ce qui prouve qu'il fait ce qu'il annonce.

## Le contrat du module

| Entrée | Type | Défaut | Effet |
| --- | --- | --- | --- |
| `prefixe` | `string` | aucun, **requis** | base de l'étiquette, **au moins 3 caractères** |
| `suffixe` | `string` | `""` | ajouté derrière un **tiret** quand il n'est pas vide |
| `majuscules` | `bool` | `false` | passe l'étiquette en **majuscules** |

Sorties : `etiquette`, la chaîne composée, et `longueur`, son nombre de
caractères.

## Les quatre comportements à couvrir

1. **Le défaut** : avec le seul `prefixe = "atelier"`, l'étiquette vaut
   `atelier`, et sa longueur `7`.
2. **Le suffixe** : avec `suffixe = "nord"`, elle vaut `atelier-nord`.
3. **Les majuscules** : avec `majuscules = true`, elle vaut `ATELIER`.
4. **Le refus** : un `prefixe` de moins de trois caractères doit faire **échouer**
   la configuration. Ce quatrième cas ne s'écrit pas comme les autres : il n'y a
   rien à assérer, puisque rien ne doit être produit. C'est l'échec lui-même qui
   est attendu, et il faut nommer l'objet qui doit le produire.

## Deux détails qui comptent

Un `run` applique par défaut (`command = apply`). Pour le cas 4, où l'on veut
seulement savoir si la configuration est **refusée**, un plan suffit.

La suite se lance depuis le répertoire du module :

```bash
cd etiquette
terraform test
```

Un `terraform test` qui affiche `Success! 0 passed, 0 failed.` n'a **rien**
testé : c'est le cas quand aucun fichier `.tftest.hcl` n'est trouvé.
