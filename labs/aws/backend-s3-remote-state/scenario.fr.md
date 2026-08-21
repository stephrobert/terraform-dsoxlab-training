# Scénario : un state distant, verrouillé, et lu par une autre stack

**Sous-objectif d'examen visé : 3b (remote state), avec appui sur 3d (partage de données entre configurations).**

Deux croyances font tomber les candidats sur cet objectif : que déclarer un `backend "s3"` suffit à verrouiller le state (le verrouillage est un opt-in, `use_lockfile` vaut `false` par défaut), et qu'un bloc `backend` se paramètre par des variables comme le reste du HCL. Ce lab fait échouer les deux, puis les répare.

## Capacité visée

Faire écrire à une configuration son state dans un bucket S3, avec un verrou réellement actif, en fournissant les paramètres d'accès par configuration partielle plutôt que par des valeurs nommées interdites dans le bloc `backend` ; puis faire consommer les outputs de ce state par une seconde configuration, sans recopier une seule valeur.

## D'où part l'apprenant

Floci tourne en local sur `localhost:4566` et fournit S3. `challenge/work` contient trois répertoires :

- `bootstrap/` : complet, à appliquer tel quel. Il crée le bucket de state sur Floci, active le versioning et bloque l'accès public. Son propre state reste local, par nécessité : le backend doit exister avant d'être utilisé.
- `producer/` : un `random_pet` et trois outputs déjà écrits. Le bloc `terraform {}` est piégé : le `backend "s3"` y déclare `bucket = var.backend_bucket` et n'a aucun argument de verrouillage. En l'état, `terraform init` s'arrête sur `Error: Variables not allowed`.
- `consumer/` : un bloc `data "terraform_remote_state"` dont le `backend` et tout le `config` sont en `???`, et quatre outputs qui référencent déjà `data.terraform_remote_state.producer.outputs.<nom>`.

Un fichier `producer/floci.s3.tfbackend` est fourni à moitié rempli : `region`, `use_path_style` et les `skip_*` y sont, `bucket`, `key` et le bloc `endpoints` sont en `???`. Rien n'est initialisé nulle part.

## L'état à atteindre

1. Le bucket de state existe sur Floci, versioning activé, accès public bloqué.
2. Le bloc `backend "s3"` du producer ne contient plus aucune référence à une valeur nommée : bucket, clé et endpoint arrivent par `terraform init -backend-config=floci.s3.tfbackend`.
3. Le producer n'a plus aucun `terraform.tfstate` local, et l'objet de state existe dans le bucket sous la clé attendue.
4. La configuration de backend réellement retenue par Terraform porte `type: s3`, un `endpoints.s3` pointant sur Floci, `use_path_style` à vrai et `use_lockfile` à vrai.
5. Le verrouillage est effectif : un objet `<clé>.tflock` déposé à la main dans le bucket fait échouer une opération du producer, et le retirer la fait repasser.
6. Le state du consumer contient exactement une entrée en mode donnée, de type `terraform_remote_state`, servie par le fournisseur intégré, et aucune ressource gérée.
7. Les quatre outputs du consumer valent exactement ceux publiés par le producer. Une valeur modifiée en amont, réappliquée, se propage en aval sans toucher au consumer.
8. Le consumer déclare un `defaults` pour un output que le producer **n'expose pas** : le repli est alors retenu. Attention, la formulation initiale de ce point était fausse et a été corrigée après mesure : pointé sur une clé de state **inexistante**, `defaults` ne sauve rien, Terraform rend `Error: Unable to find remote state` en code 1. Il comble une interface **incomplète**, jamais un état **absent**.
9. Les deux configurations sont idempotentes.

## Comment on le prouve

Aucun test n'ouvre un fichier `.tf` de l'apprenant, aucun ne lit une sortie humaine de Terraform.

- Le state distant : `aws s3api list-objects-v2` pointé sur l'endpoint Floci, sortie JSON, doit lister la clé du producer ; et le répertoire du producer ne doit contenir aucun `terraform.tfstate`. Les deux ensemble, jamais l'un seul.
- La configuration de backend effective : `.terraform/terraform.tfstate` est un JSON écrit par Terraform, pas du code d'apprenant. Les tests y lisent `backend.type`, `backend.config.endpoints.s3`, `backend.config.use_path_style` et `backend.config.use_lockfile`. C'est aussi ce qui prouve que la configuration partielle a bien été appliquée.
- Le verrou, par différence de codes retour : les tests déposent eux-mêmes un `.tflock` valide dans le bucket, lancent `terraform plan -lock-timeout=0s` et exigent un code retour non nul, puis suppriment l'objet et exigent le code 0. Sans `use_lockfile`, le même objet est ignoré et le plan passe : le test échoue donc précisément sur la configuration que l'énoncé veut interdire.
- Le partage de données : `terraform show -json` côté consumer, qui doit montrer une seule entrée en `mode: data`, de `type` `terraform_remote_state` et de `provider_name` `terraform.io/builtin/terraform`, et aucun objet en `mode: managed`. Puis `terraform output -json` des deux côtés, comparés valeur par valeur.
- La propagation : les tests changent une variable du producer, réappliquent, relancent le consumer et vérifient que ses outputs ont suivi. Une valeur codée en dur côté consumer ne bouge pas et fait tomber le test.
- Le repli : le consumer demande un output que le producer ne publie pas, et le test exige que la valeur rendue soit celle déclarée en `defaults`. La première version de ce contrôle remplaçait la clé de state par une clé absente ; mesuré, ce cas ne rend PAS le repli mais `Error: Unable to find remote state` en code 1, et le contrôle a donc été refait sur le cas que `defaults` couvre réellement.
- L'idempotence : `terraform plan -detailed-exitcode` doit rendre 0 sur le producer comme sur le consumer.

Un `challenge/work` laissé en l'état échoue dès le `terraform init` du producer, sur `Error: Variables not allowed`.
