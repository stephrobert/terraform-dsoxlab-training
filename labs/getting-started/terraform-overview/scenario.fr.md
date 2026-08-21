# Scénario : prouver que Terraform a une mémoire

**Sous-objectif d'examen visé : 1e (state, import, dérive).**

Un débutant croit que Terraform relit ses fichiers `.tf` et interroge l'infrastructure à chaque commande, le state n'étant qu'un cache accessoire. Ce lab démonte cette idée fausse : sans correspondance stockée dans le state, il n'y a ni plan vide, ni détection de dérive, ni identité stable des ressources déjà créées.

## Capacité visée

Établir, sur une configuration purement locale, que le state est ce qui relie le code à la réalité : démontrer qu'une seconde application ne produit aucun changement, qu'une dérive provoquée hors de Terraform est détectée puis corrigée sans perdre l'identité des ressources intactes, qu'une donnée seulement lue ne se confond pas avec une ressource gérée, et qu'un objet non déclaré reste invisible pour l'outil.

## D'où part l'apprenant

Le répertoire `challenge/work` contient :

- `versions.tf` : complet, il épingle les providers `random`, `local` et `null`.
- `main.tf` : troué. La longueur du `random_pet`, puis le `content` et le `filename` du
  `local_file`, sont en `???`. Le contenu doit être construit à partir de l'identifiant
  produit par `random_pet`, jamais recopié à la main : c'est cette référence qui crée la
  dépendance. Une source de données `local_file` lisant `inventaire.txt` est aussi à
  compléter.
- `outputs.tf` : troué. Trois sorties, le nom généré, le chemin du rapport, et une
  sortie déclarée sensible dérivée du nom.
- `inventaire.txt` : un fichier écrit à la main, que personne n'a déclaré comme
  ressource. Il sert de témoin et de cible pour la source de données.

Rien n'est initialisé : ni `.terraform/`, ni fichier de verrouillage, ni state.

## L'état à atteindre

1. Les providers sont installés et le fichier de verrouillage liste `random`, `local`
   et `null` avec des versions résolues.
2. Le state contient exactement deux ressources en mode géré, une `random_pet` et une
   `local_file`, et aucune autre.
3. Le state contient une entrée en mode donnée pointant sur `inventaire.txt` : elle est
   distincte des objets gérés et sa disparition ne détruirait rien sur le disque.
4. Le rapport existe sur le disque et son contenu porte l'identifiant exact généré par
   `random_pet` : il a donc été produit par Terraform, pas saisi.
5. La sortie sensible existe, sa valeur n'est pas révélée par l'affichage habituel mais
   figure en clair dans le state : le state est lui-même une donnée sensible.
6. Une nouvelle application ne produit aucun changement : configuration, state et disque
   sont alignés.
7. Si le rapport est supprimé hors de Terraform, la dérive est détectée : une seule
   ressource est à recréer, et l'identifiant `random_pet` survit intact.
8. Le fichier de state n'a jamais été édité à la main.

## Comment on le prouve

Les tests n'ouvrent jamais les fichiers `.tf` de l'apprenant et ne lisent jamais la sortie humaine de Terraform.

- `terraform show -json` fournit le state. Les tests comptent les entrées par mode
  (`managed` contre `data`), vérifient les types attendus et récupèrent l'identifiant
  de `random_pet` dans ses attributs.
- `terraform output -json` donne le nom et le chemin, et prouve le marquage
  `"sensitive": true` sur la troisième sortie. Les tests ouvrent le fichier pointé par
  le chemin et exigent que l'identifiant issu du state y figure.
- `terraform plan -detailed-exitcode` doit rendre le code 0 : preuve formelle de
  l'idempotence, sans interpréter une ligne de texte.
- Pour la dérive, les tests recopient le répertoire de travail avec son state dans un
  dossier temporaire, y suppriment le rapport, produisent un plan converti en JSON, et
  vérifient dans `resource_changes` qu'une seule création vise la `local_file` tandis
  que la `random_pet` reste inchangée. Le travail de l'apprenant n'est jamais modifié.
- Enfin, aucune adresse en mode géré ne doit référencer `inventaire.txt`.
