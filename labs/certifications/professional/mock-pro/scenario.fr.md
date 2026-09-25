# Scénario : Pro, examen blanc intégratif

**Objectifs d'examen visés : les six**, dans les conditions de l'épreuve réelle.

L'examen Terraform Authoring and Operations Professional dure **quatre heures**
et mêle QCM et travaux pratiques : écrire du code, diagnostiquer, réparer. La
documentation Terraform et celle des providers sont accessibles pendant
l'épreuve.

## Capacité visée

Enchaîner, dans le temps imparti et sans aide, six tâches couvrant les six
objectifs. Ce n'est pas un lab d'apprentissage : c'est une répétition générale,
à jouer une fois les six capstones réussis, et d'une traite.

## D'où part l'apprenant

`challenge/work` contient six répertoires, un par tâche, chacun volontairement
imparfait. Des fichiers déjà posés hors Terraform, une configuration qui ne
valide pas, trois copies d'un même couple de ressources, deux racines qui
s'ignorent, une configuration de provider absente, et douze questions sans
réponse.

Le lab se joue **hors ligne**, avec les providers `local` et `random` : aucune
VM, aucun compte, aucun émulateur. C'est un choix, et il a un prix, dit plus bas.

## L'état à atteindre

1. **Objectif 1** : adopter un fichier corrigé à la main sans écraser sa
   correction, et obtenir un plan stable.
2. **Objectif 2** : réparer trois fautes que `validate` nomme, remplacer trois
   ressources par une seule portée par `for_each`, et faire refuser au plan un
   port hors de la plage autorisée.
3. **Objectif 3** : exposer un contrat en sorties depuis une racine, le
   consommer depuis l'autre, sans rien recopier en dur.
4. **Objectif 4** : factoriser trois environnements dans un module local, sans
   qu'aucune ressource soit détruite ni recréée.
5. **Objectif 5** : rattacher explicitement une ressource à une seconde
   configuration du provider, poser les droits au bon endroit, et écrire une
   contrainte de version qui encadre la série.
6. **Objectif 6** : répondre aux douze questions HCP Terraform, avec un seuil
   global et une couverture des quatre sous-objectifs.

## Comment on le prouve

- **Une section de tests par tâche**, indépendante des autres : une tâche ratée
  ne fait pas échouer les suivantes, et le score dit quel objectif retravailler.
- Les preuves se lisent dans l'état : `terraform show -json`, le state, le
  fichier de verrouillage, les droits réels sur le disque.
- Trois tâches exigent un plan **stable** après travail, ce qui interdit de
  réussir par un détour qui reconstruit à chaque passage.

## Ce que ce mock ne couvre pas, et pourquoi

Les providers locaux ne savent pas importer : `local` comme `null` répondent
`Resource Import Not Implemented`. L'import est donc éprouvé ailleurs, par
`capstone1-resource-lifecycle` et `aws-import-moved-drift`, qui ont un vrai
provider. Ici, la tâche 1 éprouve l'autre moitié du même sous-objectif, la
réconciliation d'une dérive.

Pour la même raison, l'objectif 5 est éprouvé sur le rattachement et la
contrainte de version, non sur l'authentification d'un provider distant.
