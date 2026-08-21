# Scénario : ce que Terraform gère, ce qu'il se contente de lire

**Sous-objectif d'examen visé : 2b (data sources), avec appui sur 5b (configuration et versionnement des providers).**

Tant qu'on n'a pas vu un `destroy` effacer les objets gérés sans toucher à ce que la data
source lisait, on croit qu'un bloc `data` est une resource en lecture seule. Ce lab impose
les deux conséquences réelles : une data source ne crée rien, et elle est relue à chaque
plan, donc elle peut faire bouger un plan alors que le code n'a pas bougé d'une ligne.

## Capacité visée

Déclarer les providers d'une configuration avec une contrainte de version, puis écrire
dans la même configuration des blocs `resource`, que Terraform crée et gère avec un cycle
de vie complet, et un bloc `data`, que Terraform se contente de lire. Savoir référencer
l'un par `TYPE.NOM.ATTRIBUT` et l'autre par `data.TYPE.NOM.ATTRIBUT`, et savoir prédire
ce que chaque bloc devient après un `destroy`.

## D'où part l'apprenant

Le répertoire `challenge/work` contient un fichier `catalogue.txt` déjà présent sur le
disque, que Terraform n'a jamais créé : c'est l'objet « qui existe déjà » du scénario. À
côté, une configuration incomplète dont les trous portent sur ce qui décide de tout : le
bloc `required_providers`, le choix entre `resource` et `data` pour chaque bloc, et les
références entre blocs. Aucun cloud, aucune VM : les providers `local`, `null` et `random`
suffisent, `local` fournissant à la fois une resource et une data source `local_file`. Ni
`.terraform/`, ni state, ni fichier de verrouillage.

## L'état à atteindre

1. Les trois providers sont déclarés dans `required_providers` avec une contrainte de
   version pessimiste (`~>`) et installés par `init`.
2. Un bloc `data "local_file"` lit `catalogue.txt`. Il ne le crée pas et ne le gère pas.
3. Une `resource "local_file"` écrit un fichier dont le contenu dérive de ce que la data
   source a lu, via `data.TYPE.NOM.ATTRIBUT` : la dépendance est déduite du code, jamais
   écrite à la main.
4. Une `resource "random_pet"` produit une valeur connue seulement après création, et une
   `resource "null_resource"` en dépend par un `triggers` alimenté à la fois par cette
   valeur et par ce que la data source a lu.
5. Des `output` exposent séparément une valeur issue d'une resource et une valeur issue de
   la data source.
6. Juste après l'apply, un nouveau plan annonce zéro changement.
7. Après `destroy`, les fichiers créés par Terraform ont disparu, `catalogue.txt` est
   toujours là, intact.

## Comment on le prouve

Tout se lit dans les sorties machine de Terraform, jamais dans le `.tf` de l'apprenant.

- `terraform show -json` sépare les deux natures sans ambiguïté : les blocs créés sortent
  en `"mode": "managed"`, le bloc de lecture en `"mode": "data"` avec une adresse qui
  commence par `data.local_file.`. C'est la preuve centrale du lab.
- `terraform output -json` montre que la valeur produite par la resource dérive bien du
  contenu de `catalogue.txt` lu par la data source, et que les deux sorties existent.
- Plan enregistré puis relu en JSON (`plan -out` suivi de `show -json`) : juste après
  l'apply, aucune entrée de `resource_changes` ne porte d'action autre que `no-op`.
- `terraform plan -detailed-exitcode` sort en 0 juste après l'apply, puis en 2 une fois
  `catalogue.txt` modifié par le test sans qu'aucun `.tf` soit touché : la data source a
  été relue et le plan a bougé. Un retour 0 ici signifie que la valeur lue n'irrigue rien.
- Après `destroy`, `terraform show -json` ne rapporte plus aucun objet, les fichiers gérés
  ont disparu du disque, et `catalogue.txt` a conservé son contenu octet pour octet.
