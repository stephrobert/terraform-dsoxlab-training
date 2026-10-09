# Épreuve de niveau B : reprendre l'exploitation d'une plateforme

Vous reprenez l'exploitation d'une plateforme déjà en service : deux machines
libvirt, `web` et `db`, décrites dans `plateforme/` et dont le state vit dans
le stockage S3 partagé de l'équipe. L'identité de l'équipe sur ce stockage est
dans `exam.env`, et l'équipe a laissé dans `sauvegardes/` la copie du state
prise hier soir.

Cette nuit, **un incident** a touché l'exploitation. Personne ne sait lequel :
le constat fait partie du travail.

Durée indicative : **90 minutes**. Aucun indice n'est proposé.

## Ce qui est attendu

Trois résultats, vérifiés sur l'état réel des machines, du stockage et des
plans, jamais sur la forme de votre code :

- **La production est remise d'aplomb sans qu'aucune machine soit recréée.**
  Les machines gardent leur identité, elles tournent, et le plan de la
  production ne propose plus rien.
- **`dev` et `prod` sont séparés.** Un environnement `dev` existe, avec ses
  propres machines `web` et `db` (préfixe `<préfixe>-dev-` au lieu de
  `<préfixe>-prod-`), et une erreur sur l'un ne peut jamais toucher l'autre.
  L'organisation des fichiers est libre.
- **La chaîne de livraison tourne sans humain.** Livrez à la racine de votre
  répertoire de travail un script exécutable `chaine.sh`, que le harnais
  appellera ainsi :

  ```text
  ./chaine.sh <env> plan     # 0 : rien à faire · 2 : des changements à appliquer · 1 : erreur
  ./chaine.sh <env> apply    # applique le plan produit par le dernier « plan » de cet env
  ```

  Le script ne pose jamais de question, n'applique que le plan qui a été
  produit et donc relu, et ne laisse aucun fichier de plan derrière lui.

## Les exigences d'exploitation

L'équipe tient à quatre règles, que le harnais vérifiera :

1. Quand une autre exécution tient le verrou du state, votre chaîne **attend**
   qu'il soit libéré ; elle n'échoue pas tout de suite et ne le force jamais.
2. Une **sauvegarde** du state existe avant toute écriture qu'elle provoque.
3. Rien ne recrée une machine pour « réparer » le state.
4. Les deux environnements ne partagent **aucun** state.

## Comment c'est noté

Le rapport donne un verdict par compétence : `state`, `refactor`,
`environment`, `automate`. Une compétence en échec renvoie aux leçons qui
l'enseignent.

Pour faire noter : `dsoxlab check`.
