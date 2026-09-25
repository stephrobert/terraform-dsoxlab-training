# Produire un inventaire Ansible depuis le state

Terraform provisionne, Ansible configure, et l'inventaire est leur **seul point
de contact**. Tout ce qui se perd entre les deux se perd là.

La question de ce lab n'est pas « comment écrire un fichier depuis Terraform »,
elle est : **cet inventaire est-il encore vrai demain ?**

## Un provisioner produit un fichier juste une fois

La tentation est d'écrire l'inventaire avec un `local-exec` en fin d'apply. Cela
marche le jour même, et la documentation officielle range pourtant ces
provisioners au rang de **dernier recours**. Trois raisons, toutes vérifiables :

- Terraform **ne sait pas modéliser** leur comportement : rien de ce qu'ils font
  n'entre dans le plan ;
- ils ne laissent **aucune ressource** à inspecter dans le state ;
- ils ne rejouent qu'à la **création** ou à la **destruction** de leur porteuse.

Conséquence concrète : supprimez le fichier, le plan reste à zéro changement.
Changez une adresse dans le parc, le plan reste à zéro changement. L'inventaire
est juste le jour de l'apply, faux le lendemain, et **rien ne le signale**.

Un inventaire doit être une **ressource gérée** :

```hcl
resource "local_file" "inventaire" {
  filename = "${path.module}/inventaire.json"
  content  = jsonencode(local.inventaire)
}
```

Supprimez le fichier, le plan annonce sa recréation. Changez une valeur, il
annonce sa mise à jour. Détruisez, il disparaît avec le parc.

## Un type explicite refuse au plan

```hcl
variable "parc" {
  type = map(object({
    role  = string
    index = number
  }))
}
```

Une entrée sans `index` est rejetée **avant tout appel de provider**. Avec
`any`, la même faute passe le plan et casse plus loin, sur un message qui ne
nomme ni la variable ni l'entrée fautive.

C'est la différence entre une erreur qui dit quoi corriger et une erreur qui
demande une enquête.

## Une adresse se calcule, elle ne se recopie pas

```hcl
adresse = cidrhost(var.cidr_de_base, serveur.index)
```

`cidrhost` suit le réseau. Une adresse recopiée à la main est juste aujourd'hui
et fausse au premier changement de plage, **sans que rien ne le signale** : le
fichier est toujours du JSON valide, Ansible s'y connecte toujours, et il tombe
sur une machine qui n'est pas celle qu'on croit.

## `jsonencode` plutôt qu'une concaténation

Une chaîne construite à la main produit du JSON *presque* valide. Une virgule en
trop, un guillemet oublié dans un nom d'hôte, et Ansible rend une erreur de
parsing qui ne dit pas où.

`jsonencode` échappe ce qu'il faut, ferme ce qu'il ouvre, et rend un document
valide quel que soit le contenu. La règle générale : **on ne sérialise pas un
format à la main quand une fonction le fait**.

## Un fichier géré disparaît avec le parc

Un inventaire qui survit à la destruction pointe vers des machines qui
n'existent plus. Ansible s'y connectera, échouera, et le message parlera de
réseau : on cherchera une panne pendant que le vrai défaut est un fichier qui
aurait dû être supprimé.

C'est la moitié la moins spectaculaire du sujet, et c'est celle qui coûte le
plus de temps le jour où elle tombe.

## À vous de jouer

```bash
dsoxlab run first-infra-ansible
dsoxlab check first-infra-ansible
dsoxlab hint first-infra-ansible
```

**Aucun cloud, aucun hyperviseur** : le parc est simulé par des ressources dont
certains attributs ne sont connus qu'après création, comme une adresse allouée
par un ordonnanceur. C'est délibéré, une valeur devinable ne prouverait rien.

Sept tests. Les adresses ne sont pas comparées à une liste écrite dans le test :
elles sont **recalculées** depuis le CIDR, deux calculs indépendants valant
mieux qu'une constante.

Sous-objectif d'examen visé : **2e**, avec appui sur **1e**.

Référence : [Terraform et Ansible](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/premieres-infras/ansible/)
