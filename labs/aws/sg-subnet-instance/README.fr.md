# Security group : règles dédiées, for_each et subnet déterministe

Deux règles copiées-collées passent l'apply, et le groupe a l'air correct. Ce
lab porte sur ce qui ne se voit **qu'après** : une différence qui ne converge
jamais, un trafic sortant qui ne sort pas, et une instance qui change de subnet
sans qu'une ligne de code ait bougé.

Il se joue sur **Floci**, démarré par le lab sur `http://localhost:14566` :
aucun compte AWS, aucune facture.

## Ne mélangez jamais les deux styles de règles

AWS expose deux façons de décrire les règles d'un security group, et elles sont
**incompatibles** :

```hcl
# style 1 : règles inline, dans le groupe
resource "aws_security_group" "app" {
  ingress { ... }
}

# style 2 : ressources dédiées, hors du groupe
resource "aws_vpc_security_group_ingress_rule" "http" { ... }
```

Les blocs inline décrivent l'**ensemble complet** des règles du groupe. Terraform
considère donc que tout ce qui n'y figure pas est en trop, et supprime au
prochain apply ce que les ressources dédiées ont ajouté. Celles-ci les
recréeront, et ainsi de suite.

Le symptôme est une **différence perpétuelle** que personne n'arrive à faire
converger, et dont la cause n'apparaît nulle part dans le message.

La règle est simple : **choisissez un style, et un seul**. Les ressources
dédiées sont préférables, parce qu'elles se posent et se retirent une par une.

## AWS pose une règle de sortie, Terraform la retire

À la création d'un security group, AWS ajoute d'office une règle de sortie
« autoriser tout ». Terraform la **supprime**, parce qu'elle ne figure pas dans
votre configuration.

C'est cohérent, et c'est la source d'un incident classique : l'entrée
fonctionne, le groupe a l'air complet, et rien ne sort. On cherche du côté du
routage, de la passerelle NAT, du DNS, et le défaut est une règle qu'on n'a
jamais écrite parce qu'on croyait l'avoir par défaut.

```hcl
resource "aws_vpc_security_group_egress_rule" "tout" {
  security_group_id = aws_security_group.app.id
  cidr_ipv4         = "0.0.0.0/0"
  ip_protocol       = "-1"   # ni from_port ni to_port avec -1
}
```

## Un index n'est pas un choix

```hcl
subnet_id = data.aws_subnets.tous.ids[0]   # marche aujourd'hui
```

La documentation ne garantit **aucun ordre** sur les identifiants renvoyés. Le
`[0]` désigne un subnet aujourd'hui et peut en désigner un autre demain, sans
qu'une ligne de code ait bougé.

Le lab crée **deux** subnets exprès, pour qu'un tirage au sort ne puisse pas
passer pour un choix. La forme déterministe filtre sur ce qui porte le sens :

```hcl
data "aws_subnets" "publics" {
  filter {
    name   = "tag:Tier"
    values = ["public"]
  }
}
```

## `for_each` se prouve dans le state

Trois règles peuvent venir de trois blocs copiés-collés, d'un `count`, ou d'un
`for_each`. Le résultat est le même côté AWS, mais pas dans le state :

| Écriture | Ce que porte le state |
| --- | --- |
| trois blocs | trois `name` distincts |
| `count` | un `index` **entier** : 0, 1, 2 |
| `for_each` | un `index` **chaîne** : la clé de la carte |

C'est ce qui permet au lab de prouver le `for_each` **sans ouvrir un `.tf`**.

Et ce n'est pas une subtilité de test : la différence compte à l'usage. Retirer
la deuxième entrée d'un `count` décale les suivantes et **détruit puis recrée**
tout ce qui suit. Avec `for_each`, chaque règle est identifiée par sa clé, et
retirer une entrée ne touche qu'elle.

## `security_groups` n'est pas `vpc_security_group_ids`

Deux arguments qui se ressemblent et ne font pas la même chose :

- `security_groups` attend des **noms**, et ne vaut que dans le VPC par défaut ;
- `vpc_security_group_ids` attend des **identifiants**, et c'est celui qu'il
  faut dans un VPC à vous.

## À vous de jouer

```bash
dsoxlab run aws-sg-subnet-instance
dsoxlab check aws-sg-subnet-instance
dsoxlab hint aws-sg-subnet-instance
```

Aucun test n'ouvre un `.tf`. Une contre-vérification sort de Terraform :
`describe-security-group-rules` côté Floci doit renvoyer trois règles entrantes
et **une** sortante.

Sous-objectif d'examen visé : **2d**, les méta-arguments.

Référence : [security group, subnet et instance](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/sg-subnet-instance/)
