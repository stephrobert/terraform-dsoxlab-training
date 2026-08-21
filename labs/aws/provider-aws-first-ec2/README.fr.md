# Provider AWS : authentification, endpoints et tags par défaut

Le premier échec sur AWS n'est presque jamais le HCL : c'est la configuration du
provider. Où appelle-t-il, avec quelle identité, et que valide-t-il avant même
de planifier ?

Ce lab répond à ces trois questions sans compte AWS. Le provider vise un
émulateur local de l'API EC2, et les commandes tournent dans un environnement
purgé de toute variable `AWS_*`, avec un `HOME` dépourvu de `.aws` : ce qui
n'est pas écrit dans la configuration n'existe pas.

## Ce que vous saurez faire

- Épingler un provider sur une majeure, **bornée des deux côtés**, et vérifier
  la version réellement installée plutôt que celle que vous croyez avoir.
- Donner au provider une identité statique, désactiver les trois validations
  qui partiraient interroger le vrai AWS, et rediriger un service par
  `endpoints`.
- Poser des tags sur toutes les ressources d'une racine par `default_tags`, et
  savoir où ils apparaissent — et où ils n'apparaissent jamais.
- Prouver qu'une instance tourne, par l'état structuré et non par un message.

## Durée

40 minutes environ.

## Lancer le lab

```bash
dsoxlab run aws-provider-aws-first-ec2
```

L'émulateur démarre tout seul. Le travail se fait dans `challenge/work`.

```bash
dsoxlab check aws-provider-aws-first-ec2
```
