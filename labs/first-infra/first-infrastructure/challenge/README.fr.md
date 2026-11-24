# Première infrastructure, le cycle complet

## La situation

**Sous-objectif d'examen visé : 1c (exécuter `terraform apply` pour créer l'infrastructure), déroulé dans un cycle complet 1a init, 1b plan, 1c apply, 1d destroy.**

Ce lab existe pour que le cycle Terraform soit prouvé sur une ressource réelle, pas
récité. Le piège vient de l'audit du guide : `~> 0.8` n'interdit pas `0.9.x`, il
autorise l'incrément du composant le plus à droite. Qui croit l'inverse écrit un
`versions.tf` qui n'installe pas le provider qu'il pense, et son code, écrit pour le
schéma 0.9, casse dès qu'un verrou le ramène en 0.8.

## Capacité visée

Créer, observer, puis supprimer une infrastructure réelle avec Terraform, en pilotant
sciemment la version du provider et en lisant le résultat dans l'état structuré
plutôt que dans la sortie affichée à l'écran.

## D'où part l'apprenant

Le lab se joue en `shell`, dans `challenge/work`. C'est la seule section du parcours
où le provider `libvirt` est autorisé. Prérequis vérifiés avant tout le reste :
`libvirtd` actif et joignable en `qemu:///system`, utilisateur membre du groupe
`libvirt`, pool de stockage `default` défini et démarré, `terraform` et `virsh` dans
le `PATH`, accès réseau le temps du `terraform init`.

Le répertoire contient un `versions.tf` volontairement discutable, dont la contrainte
de provider doit être reprise, et un `main.tf` vide. Aucun `.terraform/`, aucun
`terraform.tfstate`, aucun `.terraform.lock.hcl`. Aucune image cloud à télécharger :
le volume est créé vierge, cela suffit à prouver le cycle.

## L'état à atteindre

Dans `challenge/work`, une configuration qui déclare :

1. un bloc `terraform` avec un `required_version` cohérent et une contrainte sur
   `dmacvicar/libvirt` qui installe sans ambiguïté la série `0.9.x`, celle dont le
   code utilise le schéma ;
2. un provider `libvirt` en `qemu:///system` ;
3. une seule ressource `libvirt_volume`, nommée `tf-lab-premiere.qcow2`, dans le pool
   `default`, au format `qcow2`, d'une capacité de 1 Gio ;
4. un `output` exposant le chemin du volume sur l'hôte, calculé depuis l'attribut de
   la ressource et non écrit en dur.

Le cycle est déroulé jusqu'au bout : `init`, plan revu, `apply`, puis `destroy` qui ne
laisse rien derrière lui.

## Comment on le prouve

Tout passe par de l'état structuré. Le `.tf` de l'apprenant n'est jamais relu, aucune
sortie humaine n'est parsée.

- `terraform plan -out=tfplan` puis `terraform show -json tfplan` : une seule entrée
  dans `resource_changes[]`, avec `change.actions == ["create"]`.
- `terraform show -json` après l'apply : `values.root_module.resources[]` compte
  exactement une ressource gérée de type `libvirt_volume`, dont les valeurs
  confirment le nom, le pool `default`, le format `qcow2` et la capacité.
- `terraform output -json` : le chemin du volume est présent, non vide, non sensible,
  et strictement égal au `path` lu dans le state.
- `terraform plan -detailed-exitcode` : code de sortie 0, donc aucune dérive.
- Le verrou `.terraform.lock.hcl` référence bien `dmacvicar/libvirt` en `0.9.x`.
- Contre-vérification hors Terraform : `virsh -c qemu:///system vol-list default`
  liste le volume au chemin annoncé par l'output.
- Nettoyage prouvé et inconditionnel : après `terraform destroy -auto-approve`,
  `terraform show -json` ne renvoie plus de `values.root_module.resources`, et
  `virsh vol-list default` ne liste plus rien pour ce lab. Le test de nettoyage
  s'exécute même si les vérifications précédentes ont échoué. Rien ne survit au lab.

## 🎯 Challenge : dérouler le cycle, et le prouver

### Point de départ

`challenge/work` contient `versions.tf` — **volontairement discutable**, à
reprendre — et un `main.tf` **vide**. Aucun `.terraform/`, aucun state, aucun
verrou.

**Prérequis** : `libvirt` joignable en `qemu:///system`, votre utilisateur dans
le groupe `libvirt`, le pool `default` défini et démarré, `terraform` et `virsh`
dans le `PATH`. Le réseau n'est nécessaire que pour le premier `init`.

**Aucune image cloud à télécharger** : le volume est créé vierge, cela suffit à
prouver le cycle.

### ✅ Objectif

1. **Reprendre la contrainte de provider** de `versions.tf` pour qu'elle
   installe sans ambiguïté la série `0.9.x`.
2. Un provider `libvirt` en `qemu:///system`.
3. **Une seule** ressource `libvirt_volume`, nommée `tf-lab-premiere.qcow2`,
   dans le pool `default`, au format `qcow2`, d'une capacité de **1 Gio**.
4. Un `output` exposant le **chemin** du volume sur l'hôte, calculé depuis
   l'attribut de la ressource et non écrit en dur.

Puis dérouler le cycle jusqu'au bout : `init`, plan **relu**, `apply`, et
`destroy` qui ne laisse rien.

### 🧭 Le piège de `versions.tf`

`~> 0.8` **n'interdit pas** `0.9.x`. L'opérateur pessimiste incrémente le
composant le plus à **droite** de ce qui est écrit :

| Contrainte | Accepte | Refuse |
|---|---|---|
| `~> 0.8` | `0.8.9`, **`0.9.9`** | `1.0.0` |
| `~> 0.9.0` | `0.9.9` | **`0.10.0`** |

Avec deux composants, c'est le **mineur** qui flotte. Or la branche 0.9 a
**réécrit le schéma** de presque toutes les ressources :

```hcl
# 0.8
size   = 1073741824
format = "qcow2"

# 0.9
capacity      = 1
capacity_unit = "GiB"
target        = { format = { type = "qcow2" } }
```

Laisser flotter le mineur, c'est laisser flotter le **langage**. Votre code
s'applique aujourd'hui et cassera chez le collègue dont le verrou a retenu
l'autre série. Le message d'erreur parlera d'un argument inattendu, jamais d'une
version.

### 🔍 Validation

```bash
dsoxlab check first-infra-first-infrastructure
```

Six tests. Le plan est enregistré puis relu en JSON, le state donne les valeurs,
et une contre-vérification sort de Terraform : `virsh` interroge l'hôte
directement, là où le state ne fait que rapporter. Le contrôle de la contrainte
reconstruit le verrou dans une **copie**, parce que `constraints` n'y est écrit
qu'à la création de l'entrée. Le dernier test déroule le `destroy` et exige que
**rien ne survive**, ni dans le state ni sur l'hôte.
