# 🎯 Challenge : dérouler le cycle, et le prouver

## Point de départ

`challenge/work` contient `versions.tf` — **volontairement discutable**, à
reprendre — et un `main.tf` **vide**. Aucun `.terraform/`, aucun state, aucun
verrou.

**Prérequis** : `libvirt` joignable en `qemu:///system`, votre utilisateur dans
le groupe `libvirt`, le pool `default` défini et démarré, `terraform` et `virsh`
dans le `PATH`. Le réseau n'est nécessaire que pour le premier `init`.

**Aucune image cloud à télécharger** : le volume est créé vierge, cela suffit à
prouver le cycle.

## ✅ Objectif

1. **Reprendre la contrainte de provider** de `versions.tf` pour qu'elle
   installe sans ambiguïté la série `0.9.x`.
2. Un provider `libvirt` en `qemu:///system`.
3. **Une seule** ressource `libvirt_volume`, nommée `tf-lab-premiere.qcow2`,
   dans le pool `default`, au format `qcow2`, d'une capacité de **1 Gio**.
4. Un `output` exposant le **chemin** du volume sur l'hôte, calculé depuis
   l'attribut de la ressource et non écrit en dur.

Puis dérouler le cycle jusqu'au bout : `init`, plan **relu**, `apply`, et
`destroy` qui ne laisse rien.

## 🧭 Le piège de `versions.tf`

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

## 🔍 Validation

```bash
dsoxlab check first-infra-first-infrastructure
```

Six tests. Le plan est enregistré puis relu en JSON, le state donne les valeurs,
et une contre-vérification sort de Terraform : `virsh` interroge l'hôte
directement, là où le state ne fait que rapporter. Le contrôle de la contrainte
reconstruit le verrou dans une **copie**, parce que `constraints` n'y est écrit
qu'à la création de l'entrée. Le dernier test déroule le `destroy` et exige que
**rien ne survive**, ni dans le state ni sur l'hôte.
