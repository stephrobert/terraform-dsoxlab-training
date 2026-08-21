# Une chaine jugee sur ses codes de retour

Une CI n'a pas de clavier et ne lit pas la sortie coloree. Elle decide sur des
**codes de retour**. Ce lab vous fait batir la chaine, puis **consigner** ce que
Terraform repond vraiment.

## Les cinq etapes

| # | Etape | Ce qu'elle apporte |
| --- | --- | --- |
| 1 | `fmt -check -recursive` | le depot reste lisible |
| 2 | `init -input=false` | aucune attente de saisie |
| 3 | `validate -json` | un diagnostic exploitable par une machine |
| 4 | `plan -out=... -detailed-exitcode` | la DECISION, et l'artefact a appliquer |
| 5 | `apply <fichier>` | on deploie ce qui a ete revu |

## Ce qu'il faut produire

Six fichiers de preuves, dans `preuves/`. Chacun consigne des faits **releves**,
jamais recopies depuis un cours.

| Fichier | Ce qu'il consigne |
| --- | --- |
| `chaine.json` | le code de retour de chacune des cinq etapes |
| `codes.json` | les trois valeurs de `plan -detailed-exitcode`, et le code de `fmt -check` sur un fichier mal indente |
| `prompt.json` | le code ET le temps d'attente d'un `plan -input=false` sans valeur de variable |
| `plan_fige.json` | le sort de quatre options passees a l'apply d'un plan SAUVEGARDE |
| `verrou.json` | le defaut de `-lock-timeout`, et le code d'un plan lance PENDANT un apply |
| `fuite.json` | le chemin JSON exact ou le secret sort en clair du plan sauvegarde |

## Le format attendu

```json
// preuves/codes.json
{
  "plan_avant_apply": 0,
  "plan_apres_apply": 0,
  "plan_config_cassee": 0,
  "fmt_check_mal_indente": 0
}
```

```json
// preuves/prompt.json
{ "code": 0, "attente_secondes": 0.0 }
```

```json
// preuves/plan_fige.json
{
  "var": "erreur",
  "destroy": "erreur",
  "refresh_false": "erreur",
  "target": "erreur"
}
```

Les valeurs admises sont **`erreur`** (la commande echoue) et **`ignore`** (elle
est acceptee, et sans effet sur ce qui est fait).

```json
// preuves/verrou.json
{ "defaut_secondes": 0, "code_avec_defaut": 0, "code_avec_delai": 0 }
```

```json
// preuves/fuite.json
{ "chemin": "" }
```

Le `chemin` est une expression `jq` designant l'endroit ou la valeur du secret
apparait dans `terraform show -json <plan>`.

## Trois choses a ne pas supposer

Le code de `fmt -check` sur un fichier mal indente **n'est pas 1**.

Un `plan -input=false` sans valeur de variable **n'attend pas** : mesurez son
temps.

A l'apply d'un plan sauvegarde, **une seule** des quatre options fait echouer la
commande. Les autres sont acceptees, et **ignorees**.

## Enfin

L'apply doit durer **au moins dix secondes**, sans quoi aucun verrou ne sera
observable. Et le `.gitignore` doit reellement exclure le fichier de plan :
`git check-ignore -v tfplan` le dira.
