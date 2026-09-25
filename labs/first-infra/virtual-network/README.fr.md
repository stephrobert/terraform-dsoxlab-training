# La dépendance que Terraform ne peut pas deviner

Terraform déduit l'ordre des opérations tout seul, et il le fait bien. Il
construit un graphe à partir des **références qu'il trouve dans les
expressions** : si une VM lit l'attribut d'un réseau, le réseau est créé
d'abord, sans que personne n'ait à le demander.

C'est pourquoi la documentation fait de `depends_on` un **recours de dernier
ressort**, et pourquoi le guide a raison de dire qu'il serait redondant sur un
réseau NAT déjà référencé.

Ce lab porte sur le cas symétrique : celui où plus **aucune** référence
n'exprime la dépendance, et où Terraform est donc libre d'agir dans le mauvais
ordre.

## Deux dépendances qui ne se ressemblent pas

**La dépendance implicite** naît d'une référence. Elle est visible dans le code,
et Terraform la voit aussi :

```hcl
output "passerelle" {
  value = libvirt_network.lab.addresses[0]   # une arête dans le graphe
}
```

**La dépendance comportementale** n'est visible nulle part. Le bloc consomme une
**variable**, pas un attribut :

```hcl
resource "null_resource" "rapport" {
  provisioner "local-exec" {
    command = "virsh net-dumpxml ${var.nom_du_reseau} > rapport.xml"
  }
}
```

Ce bloc a besoin du réseau. Mais il ne lit rien du réseau : il lit
`var.nom_du_reseau`. Pour Terraform, les deux blocs sont **indépendants**, et
rien ne l'empêche de lancer le rapport en premier.

## L'échec est silencieux, et c'est le sujet

Quand il le fait, `virsh net-dumpxml` échoue sur un réseau qui n'existe pas
encore, la redirection crée quand même un fichier **vide**, et Terraform annonce
`Apply complete!`.

Rien ne le signale. C'est le genre de défaut qui passe la revue, marche une fois
sur deux selon l'ordre que Terraform choisit ce jour-là, et casse en production
le jour où il choisit l'autre.

La correction est le méta-argument, et c'est ici l'un des rares endroits où il
est le bon outil :

```hcl
depends_on = [libvirt_network.lab]
```

## La règle habituelle dit l'inverse

Neuf fois sur dix, un `depends_on` écrit à la main signale une **référence
manquante**. Il suffit alors de référencer l'attribut pour que l'arête
apparaisse, et le méta-argument devient un pansement sur un code qui aurait pu
être juste.

Avant d'en écrire un, la question est donc toujours la même : **y a-t-il un
attribut que je pourrais référencer à la place ?** Si oui, référencez-le. Ce lab
porte sur la dixième fois, celle où la réponse est non.

## Ce que le plan expose de la compréhension de Terraform

Le plan converti en JSON ne montre pas seulement ce qui va être fait, il montre
**ce que Terraform a compris** de votre configuration :

```console
$ terraform show -json tfplan | jq '.configuration.root_module.outputs'
$ terraform show -json tfplan | jq '.configuration.root_module.resources[].depends_on'
```

Les `references` de chaque output prouvent la dépendance implicite. Le
`depends_on` de la ressource prouve la dépendance déclarée. Le lab vérifie aussi
que ce `depends_on` est la **seule** chose qui relie les deux blocs : posé à
côté d'une référence, il ne prouverait rien du tout.

## À vous de jouer

```bash
dsoxlab run first-infra-virtual-network
dsoxlab check first-infra-virtual-network
dsoxlab hint first-infra-virtual-network
```

**Prérequis** : `libvirt` joignable en `qemu:///system`, votre utilisateur dans
le groupe `libvirt`, `virsh` sur le `PATH`. Aucune image disque, aucune VM : le
lab reste au niveau réseau, et le réseau est détruit en sortie quoi qu'il
arrive.

Sous-objectif d'examen visé : **2d**, les méta-arguments.

Référence : [créer un réseau virtuel](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/reseau-virtuel/)
