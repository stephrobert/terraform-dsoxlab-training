# Le workflow d'un run, joué en deux temps puis qualifié

## La situation

**Sous-objectif d'examen visé : 6a, analyser le workflow d'un run HCP Terraform.**

L'objectif 6 est évalué en QCM : ni compte HCP Terraform, ni run distant. Mais un run est
avant tout une **division stricte entre un plan et un apply**, où l'apply reprend le plan
déjà calculé au lieu d'en refaire un. Cette division se joue en local, avec les plans
enregistrés, et c'est par là que ce lab commence.

Une équipe vient de passer à HCP Terraform. Ses runs s'appliquent parfois d'eux-mêmes,
attendent parfois, se terminent parfois sans rien appliquer, et personne ne sait dire à
l'avance lequel des trois va se produire.

## Capacité visée

Jouer un run en deux temps et constater ce que le plan enregistré refuse, puis déterminer,
pour un run décrit, s'il s'applique automatiquement, s'il attend une confirmation, s'il se
termine sans apply, ou s'il n'existe même pas. Et remettre les onze étapes d'un run dans
l'ordre que la documentation donne.

## D'où part l'apprenant

`challenge/work` contient deux répertoires :

1. `run/`, avec une configuration fournie : une ressource `local_file` dont le contenu
   vient d'une variable. Rien à y modifier, tout à y jouer.
2. `analyse/`, six runs décrits dans `situations.auto.tfvars.json` (déclencheur, réglage
   d'auto-apply, mode d'exécution, présence de changements dans le plan, permission
   d'appliquer), avec `verdicts.tf`, `etapes.tf` et `faits.tf` troués de `???`.

## L'état à atteindre

1. Un premier run est joué dans `run/` : son plan est enregistré dans `run1.tfplan`, et
   l'apply de **ce plan** crée `rapport.txt` contenant `premier-run`.
2. Un second run est planifié dans `run2.tfplan` avec `second-run`, et il **reste en
   attente** : le fichier sur le disque porte toujours la valeur du premier run.
3. L'output `verdicts` qualifie les six runs avec cinq mots et pas un de plus :
   `plan_speculatif`, `planned_and_finished`, `apply_automatique`, `attend_confirmation`,
   `aucun_run_distant`. Une pull request est spéculative quoi que dise le réglage
   d'auto-apply ; un plan sans changement termine le run ; un run trigger ne donne pas
   droit à l'auto-apply.
4. `etapes_du_run` donne les onze étapes dans l'ordre, la vérification OPA **avant**
   l'estimation de coût et celle de Sentinel **après**.
5. `faits` établit les deux opérations qui ne bloquent pas la file de runs, la seule étape
   où l'échec d'une run task n'arrête plus le run, et ce que fournit encore un workspace
   dont le mode d'exécution vaut `local`.

## Comment on le prouve

La moitié « run » lit le disque et les plans enregistrés, par `terraform show -json` :
l'état du système, jamais les commandes tapées. Trois propriétés mesurées le 2026-09-25 sur
Terraform 1.16.1 la portent :

- appliquer un plan enregistré n'ouvre aucune confirmation, parce que le plan a déjà
  tranché ;
- rejouer le même plan après l'apply est refusé par `Saved plan is stale`, le pendant local
  de la file de runs d'un workspace ;
- passer `-var` à l'apply d'un plan enregistré est refusé par `Can't change variable when
  applying a saved plan`, le pendant du verrouillage d'un run sur sa configuration version
  et son jeu de variables.

Ces deux derniers tests ne peuvent pas être verts avant le travail : sans apply, le premier
plan n'est pas périmé, et sans plan enregistré il n'y a rien à rejouer. Vérifié en dégradant
la solution : appliquer le second plan au lieu de le laisser en attente fait tomber le score
à 12/15, et un `apply` qui ne passe jamais par un plan enregistré le fait tomber à 12/15
également.

La moitié « analyse » ne lit que `terraform output -json`. Les six cas sont bâtis pour
qu'aucune réponse constante ne passe, et chacun est asséré séparément pour que le message
dise lequel est faux. Chaque chiffre et chaque règle viennent de la documentation
officielle, lue le 2026-09-25, et les tests portent ces liens dans leurs messages d'échec.

## 🎯 Challenge : jouer un run, puis en qualifier six autres

### 📦 Point de départ

`challenge/work` contient deux répertoires. **Aucun compte nécessaire** : la
moitié « run » se joue en local, avec les plans enregistrés.

| Fichier | État |
| --- | --- |
| `run/versions.tf`, `run/main.tf` | **fournis**, à ne pas modifier |
| `analyse/situations.auto.tfvars.json` | **fourni**, six runs décrits |
| `analyse/variables.tf`, `analyse/versions.tf` | **fournis** |
| `analyse/verdicts.tf` | un `???` : l'issue de chaque run |
| `analyse/etapes.tf` | un `???` : les onze étapes, dans l'ordre |
| `analyse/faits.tf` | trois `???` : des faits à établir |

### ✅ Objectif

1. **Jouer un premier run** dans `run/` : enregistrer son plan dans
   `run1.tfplan` avec le message `premier-run`, puis appliquer **ce plan**.
2. **Planifier un second run** dans `run2.tfplan` avec le message `second-run`,
   et le **laisser en attente**. C'est un run arrêté en « Needs Confirmation » :
   planifié, pas appliqué.
3. **Conserver les deux fichiers de plan.** Ce sont eux qui prouvent le travail.
4. **Qualifier les six runs**, avec cinq mots et pas un de plus :
   `plan_speculatif`, `planned_and_finished`, `apply_automatique`,
   `attend_confirmation`, `aucun_run_distant`.
5. **Ordonner les onze étapes**, et **établir trois faits**.

### 🧭 Essayez ce qui est refusé

Une fois le premier run appliqué, essayez de rejouer son plan. Et essayez de
passer un `-var` à l'apply du second. Les deux sont refusés, et chacun de ces
refus a un pendant dans HCP Terraform : la file de runs d'un workspace, et un run
verrouillé sur son jeu de variables.

Ces deux messages d'erreur méritent d'être lus en entier. Ils disent davantage de
ce qu'est un run que n'importe quelle définition.

### ⚠️ Aucune réponse constante ne passe

| Réponse uniforme | Échoue sur |
| --- | --- |
| `attend_confirmation` partout | les quatre autres cas |
| `apply_automatique` partout | cinq des six |
| `plan_speculatif` partout | cinq des six |

Deux pièges en particulier : le réglage d'auto-apply ne fait rien appliquer à une
pull request, et il n'applique pas un plan qui ne porte aucun changement.

### 🔍 Validation

```bash
dsoxlab check hcp-terraform-hcp-terraform-overview
```

Quinze tests. La moitié « run » lit le disque et les plans enregistrés par
`terraform show -json` ; le reste lit `terraform output -json`, donc ce que votre
configuration **calcule**, jamais ce qu'elle contient.

Bloqué ? `dsoxlab hint hcp-terraform-hcp-terraform-overview`.
