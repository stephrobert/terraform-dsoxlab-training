# 🎯 Challenge : un lot en fin de vie, quatre décisions différentes

## 📦 Le point de départ

`challenge/work` contient un projet complet, mais **jamais appliqué**. C'est à
vous de le mettre en route :

```bash
terraform init
terraform apply
```

Huit adresses entrent alors dans le state, et sept fichiers apparaissent sur le
disque :

| Adresse | Fichier | Ce qu'il doit devenir |
| --- | --- | --- |
| `random_pet.jeton` | (aucun) | reste géré, du début à la fin |
| `local_file.rapports["mensuel"]` et `["annuel"]` | `rapport-*.txt` | **légués** : hors du state, fichiers conservés |
| `local_file.bacs["beta"]` | `bac-beta.txt` | **légué**, lui seul parmi les trois bacs |
| `local_file.bacs["alpha"]` et `["gamma"]` | `bac-*.txt` | restent gérés |
| `local_file.cache` | `cache.txt` | **détruit**, fichier compris |
| `local_file.journaux` | `journaux.txt` | migration **écrite mais pas appliquée** |

Deux fichiers, deux statuts : `main.tf` est complet et **à modifier** (retirer un
bloc `resource`, retirer une clé d'un `for_each`), `migration.tf` porte deux
blocs `removed` **livrés en commentaire** et troués de `???`. Un troisième bloc
est à écrire de zéro.

**La note laissée dans `migration.tf` est fausse.** Elle prétend qu'un bloc
`removed` se contente de retirer du state et qu'il faudrait `destroy = true`
pour détruire. Ne la croyez pas : lisez le plan.

## ✅ Objectif

Mener la migration de ce lot en décidant, ressource par ressource, si l'objet
réel survit ou disparaît, et employer la bonne voie pour chaque grain.

## 📋 Ce qu'il faut obtenir

1. Le state ne porte plus que **quatre adresses** : `random_pet.jeton`,
   `local_file.bacs["alpha"]`, `local_file.bacs["gamma"]` et
   `local_file.journaux`.
2. Les **six fichiers légués** existent toujours, avec le contenu écrit lors du
   premier `apply` : les deux rapports, les trois bacs et le journal.
3. `cache.txt` a **disparu** du disque, et son adresse du state.
4. Seule la clé `beta` est sortie de `local_file.bacs`, et elle **ne figure plus
   dans le `for_each`** : sans cet alignement, Terraform recrée l'instance et
   écrase le fichier légué.
5. La migration de `local_file.journaux` est **préparée, pas appliquée** : son
   bloc `resource` a disparu, son bloc `removed` est écrit, et
   `terraform plan -detailed-exitcode` sort en **code 2** avec un unique
   changement, `forget` sur cette adresse.

## ⚠️ Le cœur du sujet

Deux frontières décident de tout, et aucune n'est devinable :

| Ce que vous voulez | Ce qu'il faut écrire |
| --- | --- |
| Léguer un objet (il survit) | `removed` + `lifecycle { destroy = false }` |
| Supprimer un objet | `removed` seul, ou `destroy = true` |
| Sortir **une seule instance** d'un `for_each` | `terraform state rm`, puis retirer la clé du `for_each` |

Le bloc `removed` refuse une clé d'instance dans son `from`
(`Resource instance keys not allowed`), et il **détruit par défaut**. Une erreur
sur ce point ne se rattrape pas : le fichier est supprimé, et les tests le
verront.

## 🔍 Validation

`dsoxlab check state-removed-block` prouve, par exécution :

- le state porte **exactement** les quatre adresses attendues ;
- les six fichiers légués existent et portent toujours le **jeton lu dans le
  state** : un fichier recréé aurait un autre contenu ;
- `cache.txt` est bien absent, du disque comme du state ;
- aucun changement en attente sur les bacs, ce qui prouve l'alignement du
  `for_each` ;
- exactement un changement en attente, `forget` sur `local_file.journaux`, et
  `plan -detailed-exitcode` en **code 2** ;
- deux contrôles de comportement joués dans une copie temporaire, sans toucher à
  votre travail.

Aucun test n'ouvre vos fichiers `.tf` : ils lisent le state, le disque et des
plans enregistrés.

Bloqué ? `dsoxlab hint state-removed-block`.
