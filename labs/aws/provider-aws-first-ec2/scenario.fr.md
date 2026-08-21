# Scénario : faire parler le provider AWS à un émulateur local

**Sous-objectif d'examen visé : 5c (authentification du provider), 5b en second (versionnement et sourcing).**

Le premier échec sur AWS n'est jamais le HCL, c'est la configuration du provider : où il appelle, avec quelles
identités, et ce qu'il valide avant même de planifier. Ce lab traite ce piège en visant l'émulateur local Floci,
donc sans compte AWS et sans jamais lire les credentials de la machine.

## Capacité visée

Configurer un provider `hashicorp/aws` épinglé sur la majeure courante pour qu'il s'authentifie et dialogue avec
une implémentation locale de l'API : identifiants statiques factices, redirection par `endpoints`, désactivation
des validations qui appellent le vrai AWS, tags posés par `default_tags`, puis créer une instance et prouver
qu'elle tourne réellement.

## D'où part l'apprenant

Prérequis : Floci écoute sur `http://localhost:14566` (`floci/floci:1.6.0`), lancé avec `-u root` et
`/var/run/docker.sock` monté. Sans cela, l'instance reste bloquée en `pending`, Floci créant un vrai conteneur
de support derrière chaque `RunInstances`.

`challenge/work` contient cinq fichiers, dont deux sont troués. `terraform.tf` déclare le provider sous le nom
local `aws` mais laisse `???` sur `source` et sur `version`. `providers.tf` est réduit à un bloc
`provider "aws"` ne portant que `region = var.aws_region` : ni identifiants, ni `endpoints`, ni argument
`skip_*`, ni `default_tags`. Sont complets : `variables.tf` (`aws_region`, `ami_id`, `instance_type`,
`floci_endpoint`, `common_tags`) et `main.tf`, dont l'unique ressource `aws_instance "lab"` consomme déjà
`var.ami_id` et `var.instance_type`. `outputs.tf` a trois blocs `output` dont les `value` valent `???`. Ni
`.terraform/`, ni state, ni `.terraform.lock.hcl`. Le lab n'utilise volontairement ni `data "aws_ami"` ni
`data "aws_caller_identity"` : Floci ignore l'AMI demandée et retombe sur son image de base.

## L'état à atteindre

1. Le provider installé est `registry.terraform.io/hashicorp/aws` en **6.x**, sous une contrainte bornée haut et
   bas, jamais la 5.x que traînent encore beaucoup d'exemples.
2. La configuration du provider porte des identifiants statiques factices non vides, de sorte qu'aucune variable
   d'environnement `AWS_*` ni aucun fichier `~/.aws` ne soit nécessaire.
3. Les trois validations qui interrogeraient le vrai AWS sont désactivées : validation des credentials par STS,
   interrogation de la metadata API, demande de l'identifiant de compte.
4. Un bloc `endpoints` redirige le service `ec2` vers l'adresse de Floci portée par `var.floci_endpoint`.
5. Le provider applique `var.common_tags` par `default_tags`, et non la ressource par un `tags` recopié.
6. Après apply, l'état contient exactement une ressource en `mode: managed`, de type `aws_instance`, qui a
   atteint l'état `running` et non `pending` : preuve que Floci a pu créer son conteneur de support, donc que le
   socket Docker est bien monté.
7. Les trois outputs exposent l'identifiant de l'instance, son état et son adresse IP privée, tous non vides.
8. Un plan relancé juste après l'apply n'annonce aucun changement, et après destroy l'état est vide.

## Comment on le prouve

Aucun test ne relit un fichier `.tf`, tout passe par les sorties structurées.

- Plan enregistré puis relu en JSON : `configuration.provider_config["aws"]` porte un `full_name`
  `registry.terraform.io/hashicorp/aws`, un `version_constraint` qui borne la majeure 6, et des `expressions`
  contenant `endpoints`, les trois `skip_*` à `true`, `default_tags`, et des clés d'accès de `constant_value`
  non vides. La configuration du provider se vérifie ainsi sans dépendre de ce que Floci renvoie.
- `terraform version -json` : `provider_selections["registry.terraform.io/hashicorp/aws"]` vaut au moins 6.0.0 et
  reste sous 7.0.0. Les commandes tournent dans un environnement expurgé de toute variable `AWS_*` et avec un
  `HOME` sans `.aws` : si les identifiants ne sont pas dans la configuration, le plan échoue.
- `terraform show -json` de l'état : une seule entrée, `"mode": "managed"`, `"type": "aws_instance"`. Une
  configuration laissée trouée ne produit rien du tout. Boucle bornée de
  `terraform apply -refresh-only -auto-approve` jusqu'à ce que son `instance_state` vaille `running`, avec échec
  au bout du délai : la transition n'est pas instantanée chez Floci, un `pending` définitif signe un socket
  Docker absent.
- `terraform output -json` : les trois valeurs sont présentes et non vides, celle de l'état vaut `running`.
- `terraform plan -detailed-exitcode` sort en 0 juste après l'apply, puis `terraform destroy -auto-approve` suivi
  d'une relecture de l'état ne laisse plus aucune ressource, Floci supprimant bien le conteneur au `terminate`.
