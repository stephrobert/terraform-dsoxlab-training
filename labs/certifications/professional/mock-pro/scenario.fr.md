# Scénario : Pro · Mock intégratif 4h

**Objectifs d'examen visés : les 6**, dans les conditions de l'examen réel.

L'examen Terraform Authoring and Operations Professional dure **4 heures** et
mélange QCM et travaux pratiques : écrire du code, troubleshooter, résoudre des
problèmes tirés de cas réels. La documentation Terraform et celle du provider
sont **accessibles pendant l'épreuve**.

## Capacité visée

Enchaîner, **dans le temps imparti et sans aide**, une série de tâches couvrant
les six objectifs. Ce n'est pas un lab d'apprentissage : c'est une répétition
générale, à jouer une fois les six capstones réussis.

## D'où part l'apprenant

Un dépôt de départ multi-stack, volontairement imparfait : des ressources déjà
créées hors Terraform, une configuration qui ne valide pas, de la duplication à
factoriser, un state local à migrer, et un provider mal configuré.

Floci fournit la partie cloud. Aucune ressource payante, aucun compte.

## L'état à atteindre

Une liste de tâches numérotées, chacune rattachée explicitement à un
sous-objectif d'examen, couvrant au minimum :

1. **Objectif 1** : importer l'existant et réconcilier un drift.
2. **Objectif 2** : réparer la configuration et la rendre dynamique.
3. **Objectif 3** : migrer vers un state distant et faire communiquer deux
   stacks.
4. **Objectif 4** : factoriser en module versionné sans recréer de ressource.
5. **Objectif 5** : ajouter un provider aliasé et corriger l'authentification.
6. **Objectif 6** : répondre aux questions HCP et corriger la policy.

## Comment on le prouve

- **Une suite de tests par tâche**, indépendante des autres : une tâche ratée ne
  doit pas faire échouer les suivantes.
- Un **score global** rendu à la fin, tâche par tâche, pour identifier les
  objectifs à retravailler.
- Les mêmes exigences que partout : preuve par l'état en JSON, idempotence,
  destroy propre.
- Le temps est un critère : le mock n'a d'intérêt que joué d'une traite.
