# 🎯 Challenge : un state distant, verrouillé, et lu

## 📦 Le point de départ

L'émulateur S3 tourne déjà sur `http://localhost:14566` : `dsoxlab` le démarre
tout seul. Aucun compte AWS n'est nécessaire.

| Répertoire | Ce que c'est |
| --- | --- |
| `bootstrap/` | **complet**, à appliquer tel quel. Son state reste **local**, par nécessité |
| `producer/` | trois outputs écrits, et un bloc `terraform {}` **piégé deux fois** |
| `consumer/` | un bloc `data` **troué**, et quatre outputs déjà écrits |
| `producer/floci.s3.tfbackend` | fourni **à moitié rempli** |
| `CIBLE.md` | l'état à atteindre, et l'ordre des opérations |

## ✅ Ce qu'il faut obtenir

1. Le bucket existe, versioning actif, accès public bloqué.
2. Le bloc `backend "s3"` ne référence plus **aucune** valeur nommée.
3. Le producer n'a **plus aucun** state local, et l'objet est dans le bucket.
4. La configuration retenue porte `use_path_style` **et** `use_lockfile` à vrai,
   et un `endpoints.s3` sur l'émulateur.
5. Le verrou est **effectif** : un `.tflock` déposé fait échouer une opération.
6. Le consumer porte **une** entrée en `mode: data` et **aucune** ressource gérée.
7. Ses sorties valent celles du producer, et **suivent** quand l'amont change.
8. Le `defaults` rend le repli pour la sortie que le producer ne publie pas.
9. Les deux configurations sont **idempotentes**.

## ⚠️ Les deux pièges du bloc `terraform {}`

**Il référence une variable.** Lancez `terraform init` et lisez la réponse : elle
explique pourquoi la configuration partielle existe.

**Il ne demande aucun verrouillage.** Le verrou du backend S3 est un **opt-in** :
`use_lockfile` vaut `false` par défaut. Sans lui, un fichier de verrou déposé dans
le bucket est purement **ignoré**.

## 🔍 Validation

`dsoxlab check aws-backend-s3-remote-state` prouve, par exécution :

- le bucket et son **versioning**, interrogés par l'API S3 ;
- la configuration de backend **réellement retenue**, lue dans
  `.terraform/terraform.tfstate` ;
- que l'objet de state est dans le **bucket** et qu'il n'en reste **aucun** en
  local, les deux ensemble ;
- le **verrou**, par différence de codes : la validation dépose elle-même un
  `.tflock`, exige que le plan **échoue**, puis le retire et exige qu'il
  **passe** ;
- que le consumer lit bien l'**état distant**, servi par le fournisseur intégré ;
- la **propagation** : l'amont est rejoué avec une autre graine, et l'aval doit
  suivre. Une valeur recopiée reste figée et tombe.

Bloqué ? `dsoxlab hint aws-backend-s3-remote-state`.
