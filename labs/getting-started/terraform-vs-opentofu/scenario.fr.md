# Scénario : prouver la compatibilité Terraform / OpenTofu, et où elle s'arrête

**Sous-objectif d'examen visé : 5b (configuration des providers : sourcing et versionnement), avec appui sur 3a (installation et versionnement des providers).**

« Les deux outils sont compatibles » se répète partout, mais personne ne le
vérifie. Le piège traité ici est le sourcing implicite : sans
`required_providers` explicite, chaque binaire résout ses providers sur son
propre registre par défaut, et la portabilité annoncée n'est plus qu'un pari.

Le lab va plus loin que l'affirmation, et c'est son intérêt : il fait constater
que la compatibilité est **réelle sur le state** et **fausse sur le fichier de
verrouillage**.

## Capacité visée

Rendre une configuration portable entre `terraform` et `tofu` en déclarant la
source et la contrainte de version de chaque provider, puis démontrer par l'état
structuré que le state, les sorties et le plan restent équivalents d'un binaire
à l'autre, tout en mesurant ce que le passage du second outil laisse derrière
lui.

## D'où part l'apprenant

`challenge/work` contient un seul fichier, `main.tf`, **fourni et complet** :
une ressource `random_pet` de deux mots, une ressource `local_file` qui écrit
l'identifiant du pet dans `rapport.txt`, une ressource `null_resource` dont le
déclencheur dépend de cet identifiant, et une sortie `nom_animal`.

Il n'y a aucun bloc `terraform {}`, donc aucun `required_providers`, aucune
contrainte de version, aucun registre nommé. Il n'y a ni `.terraform/`, ni
state, ni fichier de verrouillage.

**Cette configuration ne s'applique pas telle quelle**, et c'est délibéré : la
ressource `random_pet` désigne son provider par un **alias**, `random.principal`.
Tant qu'aucun bloc `provider "random"` ne porte cet alias, Terraform répond
`Provider configuration not present`. Le point de départ ne peut donc valider
aucun test avant le travail, ce qui est la seule façon de garantir qu'un test
vert veut dire quelque chose.

Les deux binaires sont attendus sur le poste. Le lab se joue entièrement avec
`terraform` ; `tofu` ajoute la démonstration croisée et, s'il manque, les trois
derniers contrôles sont **ignorés explicitement**, jamais comptés en échec.

## L'état à atteindre

1. Un fichier `versions.tf` déclare `required_version`, un bloc
   `required_providers` nommant explicitement `source` et `version` pour
   `random`, `local` et `null` avec des contraintes **pessimistes**, et un bloc
   `provider "random"` portant l'alias attendu.
2. Le projet est initialisé puis appliqué : le state porte exactement trois
   ressources gérées, et `rapport.txt` existe avec la valeur du pet.
3. La sortie `nom_animal` vaut l'identifiant enregistré dans le state.
4. Juste après l'application, `plan -detailed-exitcode` sort en 0.
5. `tofu` reprend le **même state**, sans destruction ni recréation : son plan
   sort en 0 et sa lecture de `nom_animal` est identique.
6. `tofu` résout les **mêmes versions** de providers, mais sur
   `registry.opentofu.org` et non `registry.terraform.io`.
7. Après le passage de `tofu`, le fichier de verrouillage est **réécrit** sur
   son registre, et `terraform` refuse de repartir tant qu'un `init -upgrade`
   n'a pas eu lieu. Après cet `init -upgrade`, le plan revient à 0 : l'aller et
   le retour n'ont rien modifié.

## Comment on le prouve

Aucun test n'ouvre les fichiers `.tf` écrits par l'apprenant.

- Les **contraintes** se lisent dans `.terraform.lock.hcl`, que personne
  n'écrit à la main. Attention : `constraints` n'y est inscrit qu'à la
  **création** de l'entrée. Un apprenant qui lance `terraform init` avant
  d'écrire ses contraintes garde un verrou sans `constraints`, et plus rien ne
  l'y ajoute, pas même un `init -upgrade`. Les tests reconstruisent donc le
  verrou dans une **copie** du répertoire, ce qui rend la mesure indépendante de
  l'ordre dans lequel l'apprenant a travaillé.
- Le **sourcing** se lit dans `provider_selections`, rendu par
  `<outil> version -json` : les adresses y sont pleinement qualifiées, et le
  préfixe de registre diffère d'un outil à l'autre.
- L'**état** se lit dans `show -json`, les **sorties** dans `output -json`, et
  le rapport est constaté sur le disque puis confronté aux attributs du state.
- L'**idempotence** se lit dans le code retour de `plan -detailed-exitcode`,
  jamais dans une phrase.
- La **démonstration croisée** se fait sur une copie du répertoire de travail,
  et pour une raison précise : `tofu init` réécrit le verrou, ce qui rendrait le
  `terraform` de l'apprenant inutilisable jusqu'à un `init -upgrade`. Un test ne
  casse pas ce qu'il mesure.
