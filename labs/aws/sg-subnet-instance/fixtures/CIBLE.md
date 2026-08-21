# Un security group dont les regles se prouvent

Deux regles copiees-collees passent l'apply. Ce lab traite ce qui ne se voit
qu'apres : melanger les deux styles de regles, et designer un subnet par un
index qui ne garantit rien.

## L'emulateur

Il tourne en conteneur et expose l'API EC2 sur **`http://localhost:14566`**.
`dsoxlab run` et `dsoxlab check` le demarrent seuls.

## Les cinq fichiers

| Fichier | Etat |
| --- | --- |
| `versions.tf` | fourni, provider deja configure |
| `variables.tf` | fourni |
| `reseau.tf` | fourni : un VPC et DEUX subnets, taggues `public` et `private` |
| `main.tf` | TROUE : cinq blocs a completer |
| `outputs.tf` | TROUE : trois `value` a renseigner |

## Ce qu'il faut atteindre

1. Le subnet retenu est **designe par son tag** `Tier = "public"`, jamais par un
   index de liste.
2. Le security group appartient au VPC cree et **ne porte aucune regle inline** :
   son attribut `ingress` est vide dans le state.
3. Les trois flux de `var.flux_entrants` viennent d'**un seul** bloc
   `aws_vpc_security_group_ingress_rule` porte par `for_each`. On le verifie a
   l'`index` de chaque instance, qui est une **chaine** : un `count` donnerait
   des entiers, et trois blocs copies donneraient trois `name` differents.
4. Une regle de sortie explicite existe, en `ip_protocol = "-1"`, **sans**
   `from_port` ni `to_port`.
5. L'instance vit dans le subnet retenu et reference le groupe par
   **`vpc_security_group_ids`**, jamais par `security_groups`.
6. Un plan rejoue apres l'apply n'annonce rien.

## Trois pieges mesures

- Un nom de groupe **ne peut pas commencer par `sg-`** : le provider refuse avec
  `invalid value for name (cannot begin with sg-)`.
- `security_groups` attend des **noms** et ne vaut que dans le VPC par defaut ;
  `vpc_security_group_ids` attend des **identifiants**. Les deux sont des
  listes : ce n'est pas une question de cardinalite.
- Renommer un security group ne le met pas a jour, cela le **detruit et le
  recree** : `name`, `description` et `vpc_id` forcent tous le remplacement.

## Controles utiles

```bash
terraform show -json | jq '.values.root_module.resources[]
  | {address, mode, type, index}'
terraform plan -detailed-exitcode   # doit sortir en 0
```
