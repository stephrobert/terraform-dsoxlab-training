# Scénario : découper un monorepo en deux stacks qui se parlent

**Sous-objectif d'examen visé : 3d (partage de données entre configurations), avec 3b (remote state) en appui.**

Le guide compare monorepo et repo par stack sur des critères d'organisation et laisse
de côté la conséquence technique qui fait échouer les candidats : séparer les stacks
sépare les states, et une stack ne voit plus rien de l'autre tant qu'on n'a pas publié
explicitement ce qu'elle doit partager.

## Capacité visée

Faire consommer par une stack aval les valeurs produites par une stack amont, via
`terraform_remote_state`, en ré-exportant à la racine les sorties d'un module
imbriqué, et en refusant de publier une donnée sensible dans un state partagé.

## D'où part l'apprenant

`challenge/work` contient un monorepo déjà découpé mais non branché :

- `modules/reseau/` : module local fonctionnel (`random_pet`, `random_integer`,
  `local_file`) exposant `network_name` et `network_cidr`. Ne pas le modifier.
- `stacks/plateforme/` : appelle le module par chemin relatif. Le bloc contient
  une ligne `version = "???"` en trop. `outputs.tf` est vide. Un
  `random_password "db"` est déjà déclaré, sans sortie associée.
- `stacks/applicatif/` : un bloc `data "terraform_remote_state" "plateforme"`
  troué (`backend = "???"`, `config = { path = "???" }`), un `local_file` dont
  le `content` référence `???` au lieu des sorties amont, et un `outputs.tf` qui
  déclare `network_cidr` avec une valeur `???`.
- Aucun state n'existe, rien n'est initialisé.

## L'état à atteindre

1. `stacks/plateforme` s'initialise : plus aucun argument `version` à côté d'un
   `source` local, puisque cette combinaison est refusée par Terraform.
2. Le state de `stacks/plateforme` existe et contient les ressources du module
   imbriqué en `mode: managed`, dont `random_password.db`.
3. Les sorties racine de `stacks/plateforme` exposent `network_name` et
   `network_cidr`, ré-exportées depuis le module : une sortie de module imbriqué
   n'est pas lisible depuis une autre configuration.
4. Aucune sortie racine de `stacks/plateforme` ne porte le mot de passe généré.
5. `stacks/applicatif` contient dans son state une entrée `mode: data` de type
   `terraform_remote_state`, pointant sur le backend local et sur le state de la
   stack amont.
6. La sortie `network_cidr` de `stacks/applicatif` vaut exactement celle de
   `stacks/plateforme`, et le fichier généré par son `local_file` contient cette
   même valeur.
7. Les deux stacks sont idempotentes.

## Comment on le prouve

Les tests n'ouvrent jamais un fichier `.tf`. Ils lancent `terraform show -json`
dans chaque stack : présence de `random_password.db` en `mode: managed` côté
plateforme, présence d'une entrée `mode: data` de type `terraform_remote_state`
côté applicatif. Ils lancent `terraform output -json` dans les deux stacks et
comparent les valeurs : `network_cidr` doit être identique de part et d'autre, ce
qu'un apprenant ne peut obtenir qu'en branchant réellement la source de données,
puisque la valeur est tirée aléatoirement à l'apply. Le même `terraform output
-json` sert à vérifier qu'aucune sortie racine ne contient la chaîne du mot de
passe lue dans le state. Enfin, `terraform plan -detailed-exitcode` doit rendre 0
dans les deux stacks.
