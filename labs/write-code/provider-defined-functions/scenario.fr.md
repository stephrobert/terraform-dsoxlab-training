# Scénario : la fonction qui n'existe pas dans le langage

**Sous-objectif d'examen visé : 5a (architecture à plugins), avec un appui direct sur 2c (fonctions HCL).**

Depuis Terraform 1.8, un provider peut exposer ses propres fonctions, appelées par un préfixe qualifié. Le piège n'est pas la syntaxe : c'est que ce préfixe reprend le **nom local** du bloc `required_providers`, et que la fonction n'existe qu'une fois le plugin chargé, dans une version qui la contient.

## Capacité visée

Rendre appelable une fonction fournie par un plugin : déclarer la source du provider sous un nom local imposé, contraindre sa version au minimum qui expose la fonction, appeler cette fonction avec la syntaxe `provider::<nom-local>::<fonction>`, et démontrer, preuve à l'appui, que ces fonctions ne font pas partie du langage.

## D'où part l'apprenant

`challenge/work` contient une configuration qui refuse de se valider. Aucune VM, aucun compte distant, et aucun téléchargement pour le provider intégré.

- `versions.tf` : `required_version = ???`, et un bloc `required_providers` qui déclare `hashicorp/local` avec une `version = ???`. Le provider intégré n'y figure pas. Un commentaire impose le nom local à lui donner : **`tfcore`**, et non `terraform`.
- `amont.tfvars.txt` : fixture fournie, non modifiable, au format d'un fichier `.tfvars`. Elle porte `region = "eu-west-3"`, `node_count = 3`, `enable_debug = true` et `zones = ["a", "b", "c"]`.
- `locals.tf` : cinq locals dont la valeur est remplacée par `???`. Le premier lit la fixture avec `file()` et doit la décoder ; le deuxième réencode le résultat après y avoir ajouté `environment = "prod"` ; le troisième produit la représentation en syntaxe d'expression de la liste des zones ; les quatrième et cinquième testent l'existence d'un répertoire, l'un présent, l'autre absent.
- `main.tf` : une ressource `local_file` qui écrit `aval.tfvars`, dont le `content` est troué.
- `outputs.tf` : complet et non modifiable. Il expose `region`, `node_count`, `aval`, `zones_expr`, `dir_present` et `dir_absent`.
- Ni `.terraform/`, ni `.terraform.lock.hcl`, ni state.

## L'état à atteindre

1. Le provider intégré est déclaré sous la source `terraform.io/builtin/terraform`, avec le nom local `tfcore`. Les trois appels correspondants s'écrivent donc `provider::tfcore::...`. Aucun `provider::terraform::` ne peut fonctionner ici, faute de nom local qui porte ce nom.
2. `required_version` admet Terraform 1.8 et refuse tout ce qui précède : avant cette version, la syntaxe qualifiée n'existe pas.
3. La contrainte posée sur `hashicorp/local` admet la 2.5.0 ou plus récente. La fonction `direxists` a été ajoutée dans cette version précise : une contrainte du type `~> 2.4.0` produit un `init` qui réussit et un appel qui échoue.
4. L'output `node_count` vaut `3` en tant que **nombre** JSON, pas en tant que chaîne : le décodage d'un contenu `.tfvars` restitue les types, contrairement à une lecture de texte.
5. L'output `aval` vaut exactement `enable_debug = true`, `environment = "prod"`, `node_count = 3`, `region = "eu-west-3"` puis `zones = ["a", "b", "c"]`, une déclaration par ligne, dans l'ordre alphabétique des clés et avec les signes `=` alignés. Cette mise en forme n'est pas choisie par l'apprenant : elle est imposée par la fonction d'encodage, et c'est justement ce qui prouve que la valeur en sort.
6. L'output `zones_expr` vaut `["a", "b", "c"]` en syntaxe d'expression Terraform, et non le JSON compact qu'aurait produit `jsonencode`.
7. `dir_present` vaut vrai pour un répertoire existant, `dir_absent` vaut faux pour un chemin inexistant.
8. `aval.tfvars` est écrit sur disque avec le même contenu que l'output `aval`.
9. Un plan relancé juste après l'apply n'annonce plus rien.

## Comment on le prouve

Aucun test n'ouvre un fichier `.tf` de l'apprenant, aucun ne parse une sortie humaine.

- `terraform providers schema -json` est la preuve d'architecture : `provider_schemas["terraform.io/builtin/terraform"].functions` contient exactement `decode_tfvars`, `encode_expr` et `encode_tfvars`, et `provider_schemas["registry.terraform.io/hashicorp/local"].functions` contient `direxists`. Les fonctions sont donc décrites par le schéma du plugin, au même titre que ses ressources.
- `terraform metadata functions -json` est la preuve par l'absence : ce document ne liste que les fonctions du langage, environ deux cent quarante, préfixées `core::`. Le test vérifie qu'aucune des quatre fonctions employées ne s'y trouve. Une fonction absente d'ici mais présente dans le schéma d'un provider vient du plugin, sans ambiguïté possible.
- `terraform version -json` : `provider_selections["registry.terraform.io/hashicorp/local"]` est supérieur ou égal à 2.5.0. Une contrainte trop basse fait échouer ce test avant même l'apply.
- `terraform output -json` : le test contrôle le **type JSON** de `node_count` avant sa valeur, puis compare `aval` et `zones_expr` aux chaînes attendues caractère pour caractère, et vérifie que `dir_present` et `dir_absent` valent respectivement vrai et faux.
- `terraform show -json` : l'attribut `content` de la ressource de `mode: managed` et de type `local_file` est confronté à l'output `aval`, dans le même document.
- `terraform plan -detailed-exitcode` retourne 0 après l'apply.
- Un `challenge/work` laissé en l'état ne produit ni state ni output : l'appel qualifié échoue sur `Unknown provider function`, et rien ne passe.
