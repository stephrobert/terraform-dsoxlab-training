# Scénario : Pro · Objectif 6, HCP Terraform

**Objectif d'examen visé : 6** (6a le workflow d'exécution, 6b les workspaces et
la gestion des accès, 6c les credentials, 6d la policy as code et la
gouvernance).

**Particularité assumée : cet objectif est le seul évalué en QCM à l'examen.**
HashiCorp ne demande aucune manipulation hands-on de HCP Terraform. Ce TP ne
lance donc **aucune exécution distante** et ne requiert **aucun compte HCP** : il
porte sur la **lecture, le diagnostic et la correction** d'une configuration et
d'une policy.

## Capacité visée

Analyser une configuration HCP Terraform et **repérer ce qui cloche** : un
périmètre d'accès trop large, des credentials mal placés, une policy qui laisse
passer ce qu'elle devrait refuser.

## D'où part l'apprenant

Un jeu de fichiers décrit une organisation fictive : plusieurs workspaces, des
variable sets, une attribution d'accès par équipe, et une **policy as code** qui
prétend interdire certaines configurations non conformes.

Tout est fourni **en l'état, avec des défauts** : rien à provisionner, tout à
auditer.

## L'état à atteindre

1. Les défauts de **périmètre d'accès** sont identifiés et corrigés : chaque
   équipe obtient le niveau minimal nécessaire, et rien de plus.
2. Les **credentials** ne sont plus exposés au mauvais niveau : ils vivent là où
   leur portée est correcte, et les valeurs sensibles sont marquées comme telles.
3. La **policy** est corrigée : elle **refuse** effectivement une configuration
   non conforme fournie en exemple, et **accepte** la configuration conforme.
4. Les réponses aux questions de compréhension du workflow d'exécution
   (qui déclenche quoi, quand un plan est appliqué, ce qu'un run distant
   implique) sont justes.

## Comment on le prouve

- La policy est **évaluée localement** contre deux jeux d'entrée : elle doit
  refuser le non conforme et accepter le conforme. Un test qui ne vérifierait
  que l'acceptation ne prouverait rien.
- La configuration corrigée est validée structurellement : les accès et la
  portée des variables correspondent à ce qui est attendu.
- Les réponses de compréhension sont vérifiées automatiquement.

> Note de conception : l'outillage exact d'évaluation de la policy reste à
> arrêter (Sentinel ou OPA) et doit être validé en conditions réelles avant
> d'écrire les tests, comme cela a été fait pour Floci.
