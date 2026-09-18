# 🎯 Challenge : prouver que Terraform a une mémoire

## Point de départ

`challenge/work` contient quatre fichiers :

- `versions.tf` : **complet, à ne pas modifier**. Il épingle `random`, `local` et
  `null`. Le troisième n'est utilisé par aucune ressource, et doit tout de même
  se retrouver dans le fichier de verrouillage.
- `main.tf` : **troué**. La longueur du `random_pet`, puis le `content` et le
  `filename` du `local_file`, sont en `???`. Une source de données `local_file`
  est également à compléter.
- `outputs.tf` : **troué**. Trois sorties, dont une à déclarer sensible.
- `inventaire.txt` : un fichier écrit à la main, que **personne n'a déclaré**.

Rien n'est initialisé : ni `.terraform/`, ni verrou, ni state.

## ✅ Objectif

Remplacez chaque `???`, puis appliquez.

1. **`random_pet.nom`** : deux mots, séparés par un tiret.
2. **`local_file.rapport`** : son contenu doit être **construit** à partir de
   l'identifiant produit par `random_pet`, jamais recopié à la main. Le fichier
   s'écrit dans le répertoire du module.
3. **`data.local_file.inventaire`** : lisez `inventaire.txt` **sans le gérer**.
4. **Les trois sorties** : le nom généré, le chemin du rapport, et une troisième
   dérivée du nom par `upper()`, déclarée **`sensitive`**.

Après `apply`, un second `terraform plan` ne doit plus rien proposer.

## 🧭 Ce que le lab vous fait constater

- **`null` figure dans le verrou** alors qu'aucune ressource ne l'utilise :
  `required_providers` suffit à le faire installer et verrouiller.
- **Le state porte trois entrées, mais seulement deux ressources gérées.** La
  troisième est en mode `data` : Terraform ne la créera ni ne la détruira.
- **`inventaire.txt` reste invisible.** Il existe sur le disque, aucune ressource
  ne le revendique, et Terraform ne s'en préoccupe pas une seule fois.
- **Supprimez le rapport, puis planifiez** : une seule création est annoncée, et
  le `random_pet` reste en `no-op`. Son identité a survécu à la dérive.
- **La sortie sensible est masquée à l'écran et en clair dans
  `terraform.tfstate`.** Le drapeau décrit un affichage, pas une protection.

## 🔍 Validation

```bash
dsoxlab check getting-started-terraform-overview
```

Huit tests lisant `terraform show -json`, `output -json`, le fichier de
verrouillage et des codes retour : les providers verrouillés, les deux ressources
gérées, la source de données distincte, l'identifiant réellement produit par
Terraform, le masque `sensitive` face au clair du state, l'idempotence par
`-detailed-exitcode`, la dérive éprouvée sur une **copie** de votre travail, et
enfin la cohérence du state avec le disque. Aucun ne lit vos `.tf`.
