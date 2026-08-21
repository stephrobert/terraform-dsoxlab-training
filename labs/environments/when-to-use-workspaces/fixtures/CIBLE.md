# Arbitrer entre workspaces et configurations separees

La documentation est nette : les workspaces conviennent aux **variations
legeres** d'une meme infrastructure, mais pas quand les deploiements exigent des
**credentials ou des controles d'acces distincts**, ni pour **decouper un
systeme** en sous-ensembles.

Ce lab vous fait porter la decision, puis payer le prix de la decoupe : deux
configurations separees ne se parlent plus toutes seules.

## Le critere, en une phrase

> Workspaces are not appropriate for system decomposition or deployments
> requiring separate credentials and access controls.

Et la raison technique, qui explique toute la liste des impossibilites : un bloc
`backend` **ne peut referencer aucune valeur nommee**. `terraform.workspace` y
est donc inutilisable, et le backend reste le meme pour tous les workspaces d'un
repertoire.

```text
Error: Variables not allowed

  on main.tf line 3, in terraform:
   3:     path = "etats/${terraform.workspace}.tfstate"

Variables may not be used here.
```

Un bloc **`provider`**, lui, accepte les expressions : c'est pourquoi on peut
faire varier un role par workspace, mais jamais le stockage de l'etat.

## Ce que contient `challenge/work`

| Repertoire | Ce que c'est |
| --- | --- |
| `mono/` | la configuration a **arbitrer**. En LECTURE : ne l'appliquez pas |
| `socle/` | racine du socle, ses `output` sont troues |
| `app/` | racine de l'application, son bloc `data` est troue |
| `bac-a-sable/` | le cas ou les workspaces restent legitimes, `lookup` troue |

## L'etat a atteindre

| Point | Attendu |
| --- | --- |
| 1 | `socle/` est applique, suit au moins une ressource, et expose **deux** outputs non vides |
| 2 | `app/` est applique et son etat contient une ressource en `mode: data` de type `terraform_remote_state` |
| 3 | Un output de `app/` **reprend a l'identique** la valeur de l'output correspondant de `socle/` |
| 4 | `socle/` et `app/` gerent des ensembles de ressources **disjoints** |
| 5 | Ni `socle/` ni `app/` n'utilise de workspace : aucun `terraform.tfstate.d` chez eux |
| 6 | `bac-a-sable/` possede **deux** workspaces, `dev` et `prod`, appliques tous les deux |
| 7 | La taille vaut celle de `dev` sous `dev`, et celle de `prod` sous `prod` |
| 8 | Les **quatre** etats sont stables : aucun changement en attente |

## Le point 3 merite qu'on s'y arrete

Recopier la valeur du socle dans `app/` produirait le meme resultat **une fois**,
puis divergerait au premier changement du socle. La validation le verifie en
reappliquant le socle avec une autre valeur, dans une copie, et en exigeant que
`app/` suive.

La donnee doit donc **traverser** les deux etats, jamais etre dupliquee.

## Comment verifier

```bash
cd socle && terraform output -json
cd ../app && terraform output -json

terraform show -json | jq '.values.root_module.resources[] | {address, mode}'
```

Et pour les workspaces du bac a sable :

```bash
ls bac-a-sable/terraform.tfstate.d/
TF_WORKSPACE=prod terraform -chdir=bac-a-sable output -raw taille
```
