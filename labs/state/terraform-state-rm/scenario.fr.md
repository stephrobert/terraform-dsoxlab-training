# Scénario : cesser de gérer une ressource sans la détruire

**Sous-objectif d'examen visé : 1e, gérer le state (retrait, ressources orphelines, réconciliation).**

Retirer une ressource du state ne la détruit pas : elle devient orpheline, et le prochain plan voudra la recréer. Ce lab fait vivre ce piège, puis fait exécuter le même retrait par la voie déclarative que HashiCorp recommande aujourd'hui pour toute nouvelle migration. Cette seconde voie porte son propre piège, plus coûteux : le bloc `removed` **détruit par défaut**.

## Capacité visée

Sortir une ressource du contrôle de Terraform sans toucher à l'objet réel, par les deux voies : la commande `terraform state rm`, puis un bloc `removed` avec `lifecycle { destroy = false }`. Et savoir que ce garde-fou n'est pas décoratif : ni le bloc `lifecycle` ni l'argument `destroy` ne sont obligatoires, les trois écritures planifient sans erreur, et deux d'entre elles **suppriment l'infrastructure**.

## D'où part l'apprenant

Le répertoire `challenge/work` est un lab de type `shell` : providers `local` et `random` uniquement, aucune machine virtuelle, aucun accès cloud.

Il contient deux fichiers, et aucun state :

- `main.tf`, complet et applicable tel quel, avec quatre ressources : `local_file.rapport` qui écrit `rapport.txt` (cible de la voie impérative), `local_file.archive` qui écrit `archive.txt` (cible de la voie déclarative), puis `local_file.conserve` et `random_pet.identifiant`, deux témoins qui doivent rester gérés du début à la fin ;
- `retrait.tf`, qui porte un bloc `removed` **livré en commentaire** et troué de deux `???` : l'adresse visée et la valeur de `destroy`. Le bloc étant commenté, la configuration s'applique telle quelle : le premier `terraform init` puis `terraform apply` est à la charge de l'apprenant, et c'est lui qui pose l'état de départ à quatre ressources.

## L'état à atteindre

1. Le projet a été appliqué : les trois fichiers `rapport.txt`, `archive.txt` et `conserve.txt` existent avec leur contenu d'origine.
2. `local_file.rapport` a quitté le state par `terraform state rm`, et son bloc `resource` a disparu de `main.tf`, ainsi que toute expression qui référencerait ses attributs ailleurs.
3. `retrait.tf` porte un bloc `removed` décommenté et complété, visant `local_file.archive` avec `destroy = false`, et le bloc `resource` correspondant a été retiré de `main.tf`. Les deux ne peuvent pas coexister : Terraform refuse de planifier avec `Removed resource still exists`.
4. Ce retrait déclaratif a été appliqué : `local_file.archive` a quitté le state.
5. `rapport.txt` et `archive.txt` existent toujours sur le disque, contenu intact. C'est le seul résultat qui distingue un retrait d'une destruction.
6. Les deux témoins sont toujours dans le state en `mode: managed`.
7. Plus aucun changement n'est en attente.

## Comment on le prouve

Les tests s'exécutent dans `challenge/work`, n'ouvrent aucun fichier `.tf` de l'apprenant et ne parsent aucune sortie destinée à un humain.

- `terraform show -json` : les adresses `mode: managed` du module racine valent **exactement** `local_file.conserve` et `random_pet.identifiant`. Les deux cibles doivent en être absentes, les deux témoins présents.
- `rapport.txt` et `archive.txt` sont lus sur le disque et comparés à leur contenu d'origine. Un apprenant qui aurait laissé Terraform détruire un objet, en particulier en oubliant `destroy = false`, échoue ici et nulle part ailleurs.
- `terraform plan -detailed-exitcode` rejoué par les tests renvoie 0. Un code 2 signalerait soit un bloc `resource` oublié dans le code (la ressource retirée serait orpheline, et Terraform voudrait la **recréer**), soit un bloc `removed` jamais appliqué.
- Le piège de la voie impérative est prouvé par exécution, pas par un artefact que l'apprenant devrait penser à produire : le test copie `challenge/work` dans un répertoire temporaire, y redéclare `local_file.rapport`, enregistre un plan et exige `actions == ["create"]`.
- Le piège de la voie déclarative est prouvé de la même façon, sur un témoin et dans une copie : un bloc `removed` **sans** `lifecycle` doit planifier `["delete"]`, et le même bloc **avec** `destroy = false` doit planifier `["forget"]`. Ces deux tests ne notent pas le travail de l'apprenant, ils vérifient que le comportement enseigné par le lab est toujours celui de Terraform. S'ils virent au rouge, c'est le lab qu'il faut revoir, pas la copie.
- L'action `forget` n'est pas documentée dans le format JSON officiel : elle est constatée par exécution sur Terraform 1.15.4, et c'est cette mesure qui fait foi.
