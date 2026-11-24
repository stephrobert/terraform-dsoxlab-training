# Objectif 6, là où les sous-objectifs se croisent

## La situation

**Objectif d'examen visé : 6 en entier** (6a le workflow d'un run, 6b les workspaces et les
accès, 6c les identifiants, 6d la policy as code).

L'objectif 6 est le seul évalué **en QCM** : HashiCorp ne demande aucune manipulation dans
HCP Terraform. Ce capstone ne réclame donc **aucun compte**, comme les sept labs de la
section.

## Ce qu'un capstone ajoute aux sept labs

Les sept labs traitent un sous-objectif chacun. Ici, chaque situation en croise **deux**, et
c'est tout l'exercice : pris séparément, chaque champ se traite par un réflexe acquis ;
ensemble, ils se renforcent ou s'annulent, et l'ordre dans lequel on les regarde décide du
résultat.

Une équipe prépare un audit de conformité. Elle doit dire, pour sept runs décrits, ce qui
s'est réellement passé, rattacher son répertoire d'audit au bon workspace, et publier une
fiche que l'auditeur puisse vérifier sans que le jeton de service ne sorte.

## Capacité visée

Trancher une situation où plusieurs règles de l'objectif 6 s'appliquent en même temps, sans
confondre ce que chacune décide.

## D'où part l'apprenant

`challenge/work` contient trois répertoires :

1. `audit/`, sept situations décrites dans `situations.auto.tfvars.json`, chacune portant un
   déclencheur, un réglage d'auto-apply, un mode d'exécution, la présence de changements, et
   l'état d'une policy avec les deux conditions de son override. Deux fichiers troués de
   `???` ;
2. `rattachement/`, à qui il manque son bloc `cloud` ;
3. `secret/`, où une fiche de service doit être écrite sans que le jeton y entre.

## L'état à atteindre

1. `verdicts` qualifie les sept situations, avec sept mots possibles et **sept issues
   différentes** : aucune réponse constante ne passe, et il n'y a pas de majorité à jouer.
2. `gouvernance` établit ce qui autorise un override, ce que deviennent les policies en mode
   d'exécution `local`, et où vivent les identifiants d'un run.
3. `rattachement/` se rattache par son **nom** au workspace `audit-conformite` de
   l'organisation `atelier-dsoxlab`, et son `init` va jusqu'à la demande d'authentification.
4. `secret/` écrit une fiche qui porte l'empreinte du jeton et jamais le jeton, et le state
   ne contient nulle part la valeur du jeton.

## Les trois croisements qui coûtent

**Une policy `mandatory` en échec sur une pull request ne bloque rien.** Il n'y a rien à
bloquer : un plan spéculatif ne peut pas appliquer. Le réflexe « mandatory donc bloqué » se
trompe de question.

**Un `advisory` en échec n'empêche pas un auto-apply.** Le niveau d'enforcement décide d'une
seule chose, et ce n'est pas celle-là.

**Un mode d'exécution `local` rend la question des policies sans objet.** Rien ne s'exécute
chez HCP Terraform, donc aucune policy ne s'y évalue, quel que soit son niveau.

## Comment on le prouve

Les tests lisent `terraform output -json` pour l'audit, la sortie de l'initialisation pour
le rattachement, et le state pour le secret. Un test vérifie en plus que **les sept verdicts
sont tous différents** : deux cas qui recevraient la même issue signaleraient une règle qui
les confond.

Pour le rattachement, deux conditions sont exigées ensemble, parce qu'une mesure du
2026-09-25 l'impose : une configuration portant `backend` et `cloud` affiche « Required
token could not be found » **à côté** de sa faute. La marque de frontière, seule,
déclarerait donc juste une configuration cassée.

Pour le secret, le state entier est balayé, et non le seul attribut attendu : un secret
déplacé ailleurs serait tout aussi exposé. Le dernier test exerce les deux côtés, car une
fiche vidée de tout satisferait l'interdit sans plus rendre aucun service.

## 🎯 Challenge : l'audit de conformité

### 📦 Point de départ

`challenge/work` contient trois répertoires. **Aucun compte HCP Terraform.**

| Fichier | État |
| --- | --- |
| `audit/situations.auto.tfvars.json` | **fourni**, sept runs décrits |
| `audit/variables.tf`, `audit/versions.tf` | **fournis** |
| `audit/verdicts.tf` | un `???` : le verdict de chaque situation |
| `audit/gouvernance.tf` | trois `???` : des faits à établir |
| `rattachement/versions.tf` | le bloc `cloud` manque |
| `secret/main.tf` | deux `???` : la fiche et son empreinte |
| `secret/variables.tf`, `jeton.auto.tfvars` | **fournis**, à ne pas modifier |

### ✅ Objectif

1. **Qualifier les sept situations.** Sept mots sont possibles ; six suffisent,
   et chacun ne sert qu'une fois.
2. **Établir trois faits** de gouvernance.
3. **Rattacher `rattachement/`** au workspace `audit-conformite` de
   l'organisation `atelier-dsoxlab`, par son nom.
4. **Écrire la fiche de service** sans que le jeton entre dans le state.

Écrivez une **règle**, pas une liste de réponses : aucune clé de situation ne
doit apparaître dans votre expression.

### 🧭 Les règles ne commutent pas

Chaque situation croise deux sous-objectifs. L'ordre dans lequel vous posez les
questions décide du résultat, parce que chacune rend la suivante sans objet :
un workspace qui n'exécute rien n'évalue aucune policy ; un run qui ne pourra
jamais appliquer n'a rien à bloquer ; un plan sans changement n'applique rien.

### ⚠️ Six issues différentes

C'est ainsi que le capstone est bâti, et un test le vérifie. Deux situations qui
recevraient le même verdict signaleraient une règle qui les confond, pas deux cas
qui se ressemblent.

### 🔍 Validation

```bash
dsoxlab check certifications-professional-capstone6-hcp
```

Huit tests. L'audit se lit dans `terraform output -json`, le rattachement dans la
sortie de l'initialisation, et le secret dans le state, balayé en entier.

Bloqué ? `dsoxlab hint certifications-professional-capstone6-hcp`.
