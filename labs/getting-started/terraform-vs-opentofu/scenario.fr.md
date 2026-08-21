# Scénario : prouver la compatibilité Terraform / OpenTofu

**Sous-objectif d'examen visé : 5b (configuration des providers : sourcing et versionnement), avec appui sur 3a (installation et versionnement des providers).**

« Les deux outils sont compatibles » se répète partout, mais personne ne le vérifie.
Le piège traité ici est le sourcing implicite : sans `required_providers` explicite,
chaque binaire résout ses providers sur son propre registre par défaut, et la
portabilité annoncée n'est plus qu'un pari.

## Capacité visée

Rendre une configuration portable entre `terraform` et `tofu` en déclarant la source et
la contrainte de version de chaque provider, puis démontrer par l'état structuré que le
state, les sorties et le plan restent équivalents d'un binaire à l'autre.

## D'où part l'apprenant

`challenge/work` contient :

- `main.tf` : une ressource `random_pet` de deux mots, une ressource `local_file` qui
  écrit l'identifiant du pet dans `rapport.txt`, une ressource `null_resource` dont le
  déclencheur dépend de cet identifiant, et une sortie `nom_animal` ;
- aucun bloc `terraform {}`, donc aucun `required_providers`, aucune contrainte de
  version, aucun registre nommé ;
- aucun `.terraform/`, aucun state, aucun fichier de verrouillage, pas de `preuves/`.

Au moins un des deux binaires est présent sur le poste. Le lab se joue entièrement avec
un seul ; le second, s'il existe, ajoute la démonstration croisée.

## L'état à atteindre

1. Un fichier `versions.tf` déclare `required_version` et un bloc `required_providers`
   nommant explicitement `source` et `version` pour `random`, `local` et `null`, avec des
   contraintes pessimistes et aucune version flottante.
2. Le projet est initialisé puis appliqué avec le binaire disponible : le state porte
   exactement trois ressources gérées et `rapport.txt` existe avec la valeur du pet.
3. `preuves/` contient, pour chaque outil joué, `version-<outil>.json` issu de
   `<outil> version -json`, `etat-<outil>.json` issu de `<outil> show -json`,
   `sorties-<outil>.json` issu de `<outil> output -json`, et `plan-<outil>.json` obtenu
   en enregistrant un plan avec `-out` puis en le relisant en JSON.
4. Juste après l'application, `plan -detailed-exitcode` sort en 0 pour chaque outil joué.
5. Si le second binaire est présent, il est lancé sur le même state, sans destruction ni
   recréation, et produit la même série de preuves.

## Comment on le prouve

Aucun test n'ouvre les fichiers `.tf` écrits par l'apprenant. Les contrôles lisent :

- `version-<outil>.json` : la clé `provider_selections` porte les adresses pleinement
  qualifiées des providers installés. Le sourcing y devient visible, le préfixe de
  registre différant d'un outil à l'autre, et les versions retenues doivent satisfaire
  les contraintes déclarées ;
- `etat-<outil>.json` : trois ressources gérées, dont `random_pet` et `local_file`, avec
  un identifiant non vide et un chemin de rapport qui désigne un fichier présent ;
- `sorties-<outil>.json` : la sortie `nom_animal` vaut l'identifiant lu dans le state ;
- `plan-<outil>.json` : aucune action autre que `no-op`, cohérent avec le code 0 relevé ;
- comparaison croisée, menée seulement si les deux jeux de preuves existent : même
  identifiant, même valeur de sortie, plan sans changement des deux côtés et registres de
  provider distincts. Avec un seul binaire, ces contrôles croisés sont ignorés
  explicitement, jamais comptés en échec.
