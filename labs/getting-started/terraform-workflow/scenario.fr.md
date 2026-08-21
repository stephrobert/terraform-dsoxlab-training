# Scénario : lire un plan avant d'appliquer

**Sous-objectif d'examen visé : Terraform Associate 6d, générer et relire un plan d'exécution.**

Une configuration déjà appliquée doit évoluer. Avant de toucher quoi que ce
soit, il faut savoir dire lesquelles de ses ressources seront modifiées en
place et lesquelles seront détruites puis recréées.

## Capacité visée

Distinguer, dans un plan et avant tout apply, une mise à jour en place d'un
remplacement, puis exécuter exactement le plan relu grâce à un plan sauvegardé
appliqué en mode non interactif.

L'enjeu n'est pas de taper quatre commandes dans l'ordre. Un remplacement
signifie qu'un objet existant disparaît, avec tout ce qu'il porte, alors que la
sortie humaine du plan annonce les deux cas dans le même bloc de texte. La
seule lecture fiable est le champ des actions du plan converti en JSON.

## D'où part l'apprenant

Le répertoire de travail `challenge/work` contient une configuration qui
n'utilise que les providers `local`, `null` et `random` : aucune machine
virtuelle, aucun hyperviseur, aucun accès à un cloud. Elle mélange volontairement
deux familles de ressources, celles dont un changement d'attribut se règle par
une mise à jour en place et celles dont le moindre changement impose une
recréation, toutes deux pilotées par un fichier de variables.

L'apprenant part d'un répertoire non initialisé et sans state. Il doit poser
l'état de référence, puis appliquer la consigne de changement du README.

## L'état à atteindre

1. Le répertoire est initialisé et la configuration de départ est appliquée :
   un state existe et décrit toutes les ressources déclarées.
2. La valeur de variable demandée par la consigne a été changée.
3. Un plan sauvegardé `tfplan` a été produit avec `terraform plan -out=tfplan`,
   et sa conversion `plan.json` obtenue avec `terraform show -json tfplan`.
4. Un fichier `analyse.json` classe chaque adresse de ressource du plan dans
   l'une des deux catégories : mise à jour en place, ou remplacement.
5. Le plan a été appliqué depuis le fichier, sans replanification ni
   confirmation interactive, avec `terraform apply tfplan`.
6. Après cet apply, plus aucun changement n'est en attente.

## Comment on le prouve

Les tests s'exécutent dans `challenge/work` et ne lisent jamais les fichiers
`.tf` de l'apprenant, ni la sortie humaine des commandes.

- Le plan sauvegardé est rouvert par l'outil : `terraform show -json tfplan`
  doit produire un document exploitable. Un `tfplan` fabriqué à la main échoue.
- La vérité est recalculée depuis `resource_changes[].change.actions` de ce
  plan, puis comparée à `analyse.json`. Une action `update` vaut mise à jour en
  place ; toute séquence contenant à la fois `delete` et `create`, quel que soit
  son ordre, vaut remplacement. Le classement de l'apprenant doit correspondre
  exactement, adresse par adresse.
- L'état final, lu avec `terraform show -json`, porte les valeurs cibles.
- La convergence est prouvée par `terraform plan -detailed-exitcode` rejoué par
  les tests : le code de sortie attendu est `0`, c'est-à-dire un diff vide. Un
  code `2` signale un changement resté en attente, un code `1` une erreur.
