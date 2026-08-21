# 🎯 Challenge : deux ressources à ne plus gérer, aucun fichier à perdre

## 📦 Le point de départ

`challenge/work` contient un projet complet, mais **jamais appliqué**. C'est à
vous de le mettre en route :

```bash
terraform init
terraform apply
```

Quatre ressources entrent alors dans le state, et trois fichiers apparaissent
sur le disque :

| Adresse | Fichier | Rôle |
| --- | --- | --- |
| `local_file.rapport` | `rapport.txt` | à retirer par la voie **impérative** |
| `local_file.archive` | `archive.txt` | à retirer par la voie **déclarative** |
| `local_file.conserve` | `conserve.txt` | témoin, reste géré |
| `random_pet.identifiant` | (aucun) | témoin, reste géré |

Deux fichiers, deux statuts : `main.tf` est complet et **à modifier** (retirer un
bloc `resource` fait partie de l'exercice), `retrait.tf` porte un bloc `removed`
**livré en commentaire** et troué de deux `???`. C'est parce qu'il est commenté
que le premier `apply` passe : décommentez-le au moment où vous en avez besoin.

## ✅ Objectif

Faire cesser la gestion de `local_file.rapport` et de `local_file.archive` sans
qu'aucun des deux fichiers ne disparaisse du disque, en employant **une voie
différente pour chacune**.

## 📋 Ce qu'il faut obtenir

1. Le state ne porte plus **que** les deux témoins, `local_file.conserve` et
   `random_pet.identifiant`, tous deux en `mode: managed`.
2. `local_file.rapport` a quitté le state par `terraform state rm`, et son bloc
   `resource` a disparu de `main.tf` : tant qu'il y reste, la ressource est
   **orpheline** et le prochain plan veut la recréer.
3. `local_file.archive` a quitté le state par le bloc `removed` de `retrait.tf`,
   complété puis **appliqué**. Son bloc `resource` a lui aussi disparu de
   `main.tf` : les deux ne peuvent pas coexister.
4. `rapport.txt` et `archive.txt` sont toujours sur le disque, avec leur contenu
   d'origine (`rapport-origine` et `archive-origine`).
5. `terraform plan -detailed-exitcode` sort en **code 0** : plus rien en attente.

## ⚠️ Le cœur du sujet

Le bloc `removed` **détruit par défaut**. Ni le bloc `lifecycle` ni l'argument
`destroy` ne sont obligatoires, et Terraform ne vous avertit pas :

| Écriture | Action planifiée | L'objet réel |
| --- | --- | --- |
| `removed` sans bloc `lifecycle` | `delete` | **détruit** |
| `removed` avec `lifecycle { destroy = true }` | `delete` | **détruit** |
| `removed` avec `lifecycle { destroy = false }` | `forget` | conservé |

Une erreur ici ne se rattrape pas : le fichier est supprimé, et le test qui lit
son contenu le verra. Vérifiez votre plan **avant** de l'appliquer.

## 🔍 Validation

`dsoxlab check state-terraform-state-rm` prouve, par exécution :

- le state porte **exactement** les deux témoins, via `terraform show -json` ;
- `rapport.txt` et `archive.txt` existent, avec leur contenu d'origine : c'est le
  seul résultat qui distingue un retrait d'une destruction ;
- `plan -detailed-exitcode` rend **0**, donc ni orpheline ni bloc `removed`
  oublié ;
- deux contrôles de comportement, joués dans une copie temporaire et sans
  toucher à votre travail : une ressource retirée du state mais toujours
  déclarée est planifiée en `create`, et un bloc `removed` privé de
  `destroy = false` est planifié en `delete`.

Aucun test n'ouvre vos fichiers `.tf` : ils lisent le state, le disque et des
plans enregistrés.

Bloqué ? `dsoxlab hint state-terraform-state-rm`.
