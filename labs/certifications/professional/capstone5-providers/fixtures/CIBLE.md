# Ce qu'il faut obtenir

Deux configurations du **même** provider, chacune avec sa région, et chaque
ressource rattachée à la bonne.

## Les quatre exigences

1. **Une contrainte de version** sur le provider, reflétée dans le fichier de
   verrouillage.
2. **Le provider par défaut** joint l'émulateur sans aller vérifier une identité
   qui n'existe pas.
3. **Une seconde configuration**, aliasée, pour `us-east-1`.
4. **`aws_instance.archives`** est créé par cette seconde configuration, et
   `aws_instance.principal` par celle par défaut.

## Ce que le lab fait diagnostiquer

L'erreur d'authentification n'est pas donnée : elle se lit. Lancez l'`apply` et
regardez quel **service** le provider essaie de joindre, puis cherchez l'option
qui l'en dispense.

Il y en a trois, et elles ne servent pas à la même chose.
