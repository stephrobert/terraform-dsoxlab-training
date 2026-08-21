# Scénario : deux racines, deux états, un module partagé

**Sous-objectif d'examen visé : 3b (backends et configuration partielle).**

Deux répertoires d'environnement ne séparent rien tant que leurs **états** ne sont
pas distincts. Et le chemin de l'état ne peut pas être paramétré par une variable :
un bloc `backend` refuse toute valeur nommée. La configuration **partielle** est la
réponse officielle.

## Capacité visée

Câbler deux configurations racine sur un module partagé, donner à chacune son
propre état par configuration partielle du backend, puis prouver l'isolation en
détruisant l'un des deux environnements.

## D'où part l'apprenant

`challenge/work` fonctionne **hors ligne**, backend `local` :

- `modules/plaque/` : le module partagé, complet, deux entrées et deux sorties.
- `envs/dev/main.tf` et `envs/prod/main.tf` : **identiques**, avec un
  `backend "local" {}` vide déjà écrit et un appel de module troué.
- `CIBLE.md` : les valeurs attendues par environnement, l'erreur `Variables not
  allowed` qui explique le bloc vide, et la commande d'initialisation.

## L'état à atteindre

1. Chaque racine appelle le module partagé par un chemin **relatif**.
2. `dev` produit **une** plaque, `prod` en produit **trois**.
3. Chaque racine pilote son propre état, `etats/dev.tfstate` et
   `etats/prod.tfstate`, **hors** des répertoires racine.
4. Les deux backends sont configurés par `-backend-config`, le bloc restant vide.
5. Les deux environnements sont appliqués et convergent.

## Comment on le prouve

- `.terraform/terraform.tfstate` de chaque racine porte la configuration de backend
  **retenue** : son `config.path` doit différer d'une racine à l'autre et porter le
  nom de l'environnement.
- `terraform show -json` par racine : le **compte** de ressources, l'environnement
  exposé, et les chemins produits.
- Les deux `modules.json` doivent désigner le **même** dossier de module, par un
  `Source` en `../`.
- **La preuve d'isolation** : les tests copient le travail, lancent un `destroy`
  réel dans `dev`, et exigent que l'état de `prod` soit **inchangé**, adresse par
  adresse.
- `plan -detailed-exitcode` à 0 dans les deux.

Un `challenge/work` nu rend 0 sur 6. Faire pointer `prod` sur l'état de `dev` fait
tomber quatre tests, dont celui de l'isolation. Dupliquer le module dans chaque
racine ne fait tomber que celui du module partagé.
