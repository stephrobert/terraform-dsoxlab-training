# Scénario : un security group dont les règles se prouvent

**Sous-objectif d'examen visé : 2d, les meta-arguments.**

Deux règles copiées-collées passent l'apply. Ce lab traite ce qui ne se voit
qu'après : mélanger règles inline et ressources de règle dédiées, et oublier que
Terraform retire la règle de sortie qu'AWS pose par défaut.

## Capacité visée

Construire un security group dont toutes les règles sont des ressources dédiées,
les règles d'entrée venant d'un seul bloc porté par `for_each`, et attacher une
instance à un subnet désigné de façon déterministe.

## D'où part l'apprenant

**Floci doit tourner** : `docker run -d --name floci -p 4566:4566 -u root
-v /var/run/docker.sock:/var/run/docker.sock floci/floci:1.6.0`. Aucun compte
AWS, aucune facture, aucun endpoint réel. Le socket Docker et `-u root` ne sont
pas optionnels : sans eux l'instance reste bloquée en `pending`. Floci ignore
aussi l'AMI demandée : sa valeur est un bouchon, aucun test ne l'inspecte.

`challenge/work` est vierge : ni `.terraform/`, ni verrou, ni state.
`versions.tf` est complet (provider `hashicorp/aws` en `~> 6.0`, bloc
`endpoints` vers `http://localhost:4566`, les trois `skip_*`, identifiants
factices non vides) : la configuration du provider est fournie, elle n'est pas
l'objet du lab. `reseau.tf` l'est aussi : un VPC et **deux** subnets taggués
`Tier = "public"` et `Tier = "private"`, pour qu'un tirage au sort ne passe pas
pour un choix. `variables.tf` porte une carte `flux_entrants` de trois entrées,
nom vers port. `main.tf` et `outputs.tf` sont troués par des `???` : le subnet
retenu, le security group, le bloc unique de règles d'entrée, la règle de
sortie, l'attachement de l'instance et les sorties exposées.

## L'état à atteindre

1. Le répertoire est initialisé et le fichier de verrouillage existe.
2. Le VPC et les deux subnets sont en `mode: managed`. Le subnet retenu est
   désigné par une data source filtrée sur le tag `Tier = "public"`, jamais par
   un index : la doc ne garantit aucun ordre des identifiants renvoyés.
3. Le security group appartient au VPC créé et **ne porte aucune règle inline** :
   ses attributs `ingress` et `egress` sont vides dans le state. Mélanger les
   deux styles produit des différences perpétuelles et des règles écrasées.
4. Les trois règles d'entrée proviennent d'un **seul** bloc
   `aws_vpc_security_group_ingress_rule` porté par `for_each` sur
   `flux_entrants` : une plage de port et une seule CIDR par règle.
5. Une règle de sortie explicite existe (`aws_vpc_security_group_egress_rule`,
   `ip_protocol = "-1"`, **ni** `from_port` **ni** `to_port`) : sans elle,
   l'instance n'a aucune sortie, car Terraform supprime la règle « autoriser
   tout » qu'AWS crée à la naissance du groupe.
6. L'instance vit dans le subnet retenu et référence le groupe par
   `vpc_security_group_ids`, jamais par `security_groups`, qui attend des noms
   et ne vaut que dans le VPC par défaut.
7. Rejouer un plan n'annonce rien, et le state après destruction est vide.

## Comment on le prouve

Aucun test ne relit un `.tf` de l'apprenant, aucun ne parse une sortie humaine.

- `terraform show -json` classe chaque adresse du state par `mode`, ce qui
  interdit de faire passer un subnet géré pour une data source, et les attributs
  `ingress` et `egress` du security group y sont vérifiés vides.
- Les instances de la règle d'entrée sont comptées dans
  `values.root_module.resources` : trois entrées de même `type` et même `name`,
  dont le champ `index` est une **chaîne**. Un `count` donnerait des entiers, un
  copier-coller trois `name` distincts. La règle de sortie est retrouvée par son
  `type`, avec `from_port` et `to_port` attendus nuls.
- `terraform output -json` : le `subnet_id` exposé vaut l'`id` du subnet taggué
  `public`, et le `subnet_id` de l'instance dans le state lui est égal.
- `terraform plan -detailed-exitcode` sort en 0 après l'apply, et le plan de
  destruction converti en JSON ne contient aucune entrée `mode: data`. Côté
  Floci, `describe-security-group-rules` renvoie trois règles entrantes et une
  sortante pour ce groupe.
