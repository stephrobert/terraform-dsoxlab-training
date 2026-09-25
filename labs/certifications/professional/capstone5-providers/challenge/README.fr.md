# 🎯 Challenge : deux configurations d'un même provider

## 📦 Le point de départ

`challenge/work` contient un `main.tf` qui **ne s'applique pas**, et un
`CIBLE.md`. Floci fournit l'émulateur.

Trois choses manquent, et elles ne se manifestent pas au même moment :

1. **aucune contrainte de version** sur le provider ;
2. **le provider cherche une identité qui n'existe pas** : lancez un `plan` et
   lisez l'erreur, elle nomme ce qu'il n'a pas trouvé ;
3. **une exigence nouvelle** : les archives doivent vivre dans une seconde
   région, ce qu'une seule configuration ne peut pas faire.

Les deux premières se **diagnostiquent**. La troisième se **construit**.

## ✅ Objectif

1. **Une contrainte de version**, reflétée dans le fichier de verrouillage.
2. **Le provider par défaut** joint l'émulateur sans aller vérifier une identité
   inexistante : identifiants factices **non vides**, et les trois options qui
   le dispensent de chercher.
3. **Une seconde configuration**, aliasée, pour `us-east-1`. Elle porte ses
   propres options : rien ne s'hérite d'une configuration à l'autre.
4. **`aws_instance.archives`** créée par cette seconde configuration,
   `aws_instance.principal` par celle par défaut.

## 🧭 L'oubli qui ne se voit pas

Sans l'argument `provider`, une ressource utilise la configuration **par
défaut**. Elle est créée au mauvais endroit, et **rien ne le signale** : deux
instances se ressemblent, et l'état ne dit pas qui les a produites.

Le seul endroit qui le dit est le champ `provider_config_key` de la section
`configuration` du plan JSON.

## ⚠️ Le verrou ne se met pas à jour tout seul

`constraints` n'est écrit dans `.terraform.lock.hcl` qu'à la **création** de
l'entrée. Si vous ajoutez la contrainte après un premier `init`, supprimez le
verrou et relancez : ni `init`, ni `init -upgrade` ne le corrigent.

## 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone5-providers
```

Six tests, dans un environnement **sans aucun identifiant AWS** : ni variable
`AWS_*`, ni `~/.aws`. C'est ce qui fait apparaître l'erreur à diagnostiquer, et
ce qui garantit que le lab mesure votre travail et non votre poste.

Une preuve sort de Terraform : Floci **isole par région**, donc chaque instance
doit être vue dans la sienne et absente de l'autre.

Bloqué ? `dsoxlab hint certifications-professional-capstone5-providers`.
