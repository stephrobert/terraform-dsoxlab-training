# Faire parler le provider AWS a une API locale

Le premier echec sur AWS n'est presque jamais le HCL : c'est la configuration du
provider. Ou appelle-t-il, avec quelle identite, et que valide-t-il avant meme
de planifier ? Ce lab traite ce piege sans compte AWS, en visant un emulateur
local, et sans jamais lire les identifiants de votre machine.

## L'emulateur

Il tourne en conteneur et expose l'API EC2 sur **`http://localhost:14566`**.
`dsoxlab run` et `dsoxlab check` le demarrent seuls : vous n'avez rien a lancer.

Il cree un vrai conteneur derriere chaque instance demandee. Une instance qui
reste indefiniment en `pending` signe donc un emulateur mal lance, pas une faute
de votre part.

## Les cinq fichiers

| Fichier | Etat |
| --- | --- |
| `terraform.tf` | TROUE : `source` et `version` du provider valent `???` |
| `providers.tf` | REDUIT : le bloc ne porte que `region` |
| `outputs.tf` | TROUE : les trois `value` valent `???` |
| `variables.tf` | complet, ne rien y changer |
| `main.tf` | complet, ne rien y changer |

## Ce qu'il faut atteindre

1. Le provider installe est `hashicorp/aws` en **6.x**, sous une contrainte
   **bornee des deux cotes**. La 5.x que trainent encore beaucoup d'exemples
   n'est pas acceptee.
2. Des identifiants statiques factices figurent dans la configuration : aucune
   variable `AWS_*` ni aucun fichier `~/.aws` ne doit etre necessaire.
3. Les trois validations qui interrogeraient le vrai AWS sont desactivees :
   validation des identifiants par STS, appel a la metadata API, demande de
   l'identifiant de compte.
4. Un bloc `endpoints` redirige le service `ec2` vers `var.floci_endpoint`.
5. Les tags de `var.common_tags` arrivent sur l'instance **par le provider**,
   pas par un `tags` recopie sur la ressource.
6. Apres apply, l'instance a atteint l'etat `running`.
7. Les trois outputs rendent l'identifiant, l'etat et l'IP privee, tous non
   vides.
8. Un plan relance juste apres l'apply n'annonce aucun changement.

## Deux ecueils mesures

- `terraform validate` ne prouve rien ici : une configuration de provider
  incomplete le passe sans broncher, et c'est le `plan` qui echoue.
- Un tag pose sur la ressource et un tag de meme nom pose par le provider ne
  produisent **ni erreur ni avertissement** : la valeur de la ressource gagne
  en silence. C'est pourquoi `main.tf` ne declare aucun `tags`.

## Controles utiles

```bash
terraform version -json | jq '.provider_selections'
terraform plan -out=tfplan && terraform show -json tfplan \
  | jq '.configuration.provider_config.aws'
terraform show -json | jq '.values.root_module.resources[].values.instance_state'
terraform plan -detailed-exitcode   # doit sortir en 0
```
