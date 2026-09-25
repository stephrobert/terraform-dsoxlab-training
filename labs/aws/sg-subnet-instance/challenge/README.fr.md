# 🎯 Challenge : des règles qui se prouvent, un subnet qui ne se tire pas au sort

## Point de départ

`challenge/work` est vierge : ni `.terraform/`, ni verrou, ni state.

**Floci est démarré par le lab**, sur `http://localhost:14566` : aucun compte
AWS, aucune facture.

| Fichier | Ce qu'il a |
| --- | --- |
| `versions.tf` | **fourni**. Provider `~> 6.0`, `endpoints`, les trois `skip_*`, identifiants factices |
| `reseau.tf` | **fourni**. Un VPC et **deux** subnets, taggués `Tier = "public"` et `Tier = "private"` |
| `variables.tf` | **fourni**. Une carte `flux_entrants` de trois entrées, nom vers port |
| `main.tf` | **troué** : le subnet retenu, le groupe, les règles, l'instance |
| `outputs.tf` | **troué** |

Il y a **deux** subnets, et c'est délibéré : avec un seul, un tirage au sort
passerait pour un choix.

## ✅ Objectif

1. **Désigner le subnet public** par une data source filtrée sur son tag, jamais
   par un index.
2. **Un security group** dans le VPC créé, **sans aucune règle inline**.
3. **Un seul bloc** de règles d'entrée, porté par `for_each` sur
   `flux_entrants`.
4. **Une règle de sortie explicite**.
5. **L'instance** dans le subnet retenu, rattachée au groupe.
6. **Les sorties** exposant l'identifiant du subnet retenu et celui du groupe.

## 🧭 Quatre pièges, dont trois ne se voient qu'après l'apply

**Un index n'est pas un choix.** `data.aws_subnets.tous.ids[0]` marche
aujourd'hui. La documentation ne garantit **aucun ordre** sur les identifiants
renvoyés : demain, le `[0]` désigne l'autre subnet, et l'instance change de
réseau sans qu'une ligne de code ait bougé. Filtrez sur le tag.

**Ne mélangez jamais règles inline et ressources dédiées.** Les deux styles se
disputent le même objet : les blocs `ingress` du groupe décrivent l'ensemble
complet des règles, donc Terraform supprime au prochain apply tout ce que les
ressources dédiées ont ajouté. Le symptôme est une différence perpétuelle que
personne n'arrive à faire converger.

**AWS pose une règle de sortie « tout autoriser » à la création du groupe, et
Terraform la supprime.** C'est voulu, et c'est la source d'un incident
classique : le groupe a l'air correct, l'entrée fonctionne, et rien ne sort. Si
vous voulez une sortie, **déclarez-la**.

**`security_groups` n'est pas `vpc_security_group_ids`.** Le premier attend des
**noms** et ne vaut que dans le VPC par défaut. Dans un VPC à vous, c'est le
second, et il attend des **identifiants**.

## 🔍 Validation

```bash
dsoxlab check aws-sg-subnet-instance
```

Aucun test n'ouvre un `.tf`. Les trois règles d'entrée sont comptées dans le
state, et leur champ `index` doit être une **chaîne** : un `count` donnerait des
entiers, un copier-coller donnerait trois `name` distincts. C'est ainsi qu'on
prouve un `for_each` sans lire le code.

Une contre-vérification sort de Terraform : `describe-security-group-rules`
côté Floci doit renvoyer trois règles entrantes et **une** sortante.

Bloqué ? `dsoxlab hint aws-sg-subnet-instance`.
