# Comprendre le state Terraform : ce qu'il sait, ce qu'il ne cache pas

Le **state** est le lien entre votre code et le monde réel : il associe chaque
adresse (`random_password.db`) à l'objet réel correspondant. Mais il fait plus,
et c'est là que sont les pièges. Il **garde les secrets en clair**, il se
**protège** contre une réécriture par un état plus ancien, et il ne détecte une
**dérive** que s'il a **rafraîchi** juste avant. Ce tutoriel montre ces trois
faits ; le challenge vous les fera prouver.

## Reprendre la main sans recréer : le bloc `import`

Quand un objet **existe déjà** (créé à la main, ou hérité), l'appliquer tel quel
le **recrée**, ce qui peut être destructeur. Le bloc **`import`** (Terraform 1.5+)
le **rattache** au state, sans le recréer, et s'applique par `terraform apply` :

```hcl
import {
  to = random_password.db
  id = "la-valeur-existante"
}
resource "random_password" "db" {
  length = 20
}
```

Après l'apply, `random_password.db.result` porte la valeur **existante**, pas une
valeur neuve. C'est la différence entre reprendre la main et tout casser.

## Le secret est en clair dans le state

Une croyance répandue est que `sensitive` **protège** un secret. Non : il masque
seulement l'**affichage**. Dans le state, la valeur est **en clair** :

```bash
terraform state pull | jq '.resources[] | select(.type=="random_password")
  | .instances[0].attributes.result'
```

La même instance porte `result` dans son tableau **`sensitive_attributes`** : la
marque existe, mais elle ne cache **rien** du contenu du fichier de state. C'est
pourquoi un state se chiffre au repos et se stocke dans un backend protégé.

## La dérive ne se voit qu'avec un refresh

Terraform ne « surveille » pas votre infrastructure. Il ne voit une **dérive**
(un changement fait hors Terraform) que lorsqu'il **rafraîchit** le state en
relisant le monde réel, ce qu'un `plan` fait par défaut :

- `terraform plan` (avec refresh) sur un objet modifié hors Terraform rend
  **`2`** (`-detailed-exitcode`) : la dérive est vue.
- `terraform plan -refresh=false` rend **`0`** : sans relire le réel, le state
  seul ne voit rien.

Ce couple de codes est la preuve que la détection vient du **rafraîchissement**.
Une CI qui court avec `-refresh=false` pour aller vite peut donc **rater** une
dérive.

## Le state se protège : serial et lineage

Deux champs du state gardent son intégrité :

- **`serial`** s'incrémente à chaque écriture. `terraform state push` **refuse**
  un état de `serial` **inférieur** (`cannot import state with serial ... over
  newer state ...`) : on ne remet pas en place un état périmé par accident.
- **`lineage`** identifie la lignée du state. Pousser un état de `lineage`
  **différent** est aussi refusé, mais avec un message **distinct**
  (`unrelated state with lineage ...`).

Ces garde-fous existent pour empêcher un écrasement destructeur. On les force avec
`-force`, à ses risques.

## À vous de jouer

Vous savez qu'un bloc `import` reprend la main sans recréer, que le secret est en
clair dans le state malgré `sensitive`, que la dérive n'apparaît qu'avec un
refresh, et que `state push` refuse un `serial` antérieur ou un `lineage`
différent. Le challenge vous fait rattacher un mot de passe déjà en service, sans
le régénérer, et le prouve.

```bash
dsoxlab run state-understand-state
dsoxlab check state-understand-state
dsoxlab hint state-understand-state
```

Sous-objectif d'examen visé : **1e**, niveau Professional.

Référence : [Comprendre le state](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/comprendre-state/)
