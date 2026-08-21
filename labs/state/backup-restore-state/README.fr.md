# Sauvegarder et restaurer un state, sans rien recréer

Le state est un fichier, et un fichier se perd, se tronque, se remplace par
erreur. Quand cela arrive, l'infrastructure, elle, va très bien : ce sont les
enregistrements qui manquent. La réparation consiste donc à **remettre le bon
state**, pas à relancer un `apply` qui recréerait ce qui existe déjà.

Ce tutoriel montre les deux commandes qui portent cette réparation,
`terraform state pull` et `terraform state push`, les deux garde-fous que
Terraform oppose à une restauration hasardeuse, et les filets qu'il pose de
lui-même, dont un que presque personne ne connaît.

## Le terrain d'essai

Dans un répertoire à part, hors du challenge :

```hcl
terraform {
  required_version = ">= 1.7"
  required_providers {
    local = { source = "hashicorp/local", version = ">= 2.5" }
  }
}

resource "local_file" "releve" {
  filename = "${path.root}/donnees/releve.csv"
  content  = "capteur,valeur\nt1,19\n"
}

resource "local_file" "bulletin" {
  filename = "${path.root}/donnees/bulletin.txt"
  content  = "bulletin hebdomadaire\n"
}
```

Un `terraform init` puis un `terraform apply` créent deux fichiers dans
`donnees/` et un `terraform.tfstate` à la racine.

## `terraform state pull` : photographier le state

La commande écrit le state courant sur la sortie standard, **quel que soit le
backend**. Sur un backend distant, c'est le seul moyen simple d'en obtenir une
copie locale ; sur un backend local, elle a l'avantage de passer par Terraform
plutôt que par le système de fichiers.

```bash
terraform state pull > photo.json
```

Trois champs suffisent à identifier une photo, et ce sont eux qui décideront de
tout :

```json
{
  "lineage": "cf018339-7f2e-b564-8026-b9621939c826",
  "serial": 3,
  "version": 4
}
```

Le `lineage` est l'**identité de la lignée** : Terraform le tire au sort à la
création du state et ne le change plus. Deux states qui portent le même lineage
décrivent la même infrastructure au fil du temps. Le `serial` est un **compteur
d'écritures** : il s'incrémente à chaque modification du state, et permet de
dire lequel de deux fichiers est le plus récent.

## Les deux filets que Terraform pose tout seul

Le backend local écrit un `terraform.tfstate.backup` qui contient l'état
**d'avant la dernière écriture**. Beaucoup s'arrêtent là, et c'est une erreur :
ce fichier n'est mis à jour que par les opérations ordinaires, `apply` en tête.

Une commande de manipulation du state, elle, dépose un fichier **horodaté** :

```bash
terraform state rm local_file.bulletin
ls terraform.tfstate*
```

```text
terraform.tfstate
terraform.tfstate.1785258572.backup
```

Vérifié sur 1.15.4 : après ce `state rm`, `terraform.tfstate.backup` n'a **pas
bougé**, et c'est le fichier horodaté qui porte l'état complet d'avant la
commande. Conséquence pratique, et elle vaut d'être retenue : **le filet qui
vous sauvera après une manipulation de state n'est pas celui que vous croyez**.
Ces fichiers étant presque toujours gitignorés, un nettoyage de répertoire les
emporte sans que personne ne s'en aperçoive.

## `terraform state push` : réinjecter un state

La commande fait le chemin inverse du `pull`. Elle refuse deux situations, et
ces refus sont exactement ce qui protège votre infrastructure.

**Premier garde-fou, le `serial`.** Pousser un state plus ancien que le state
courant serait perdre les écritures intermédiaires :

```text
Failed to write state: cannot import state with serial 3 over newer state with serial 4
```

**Second garde-fou, le `lineage`.** Pousser un state issu d'un autre projet
détruirait le lien entre le state et l'infrastructure réelle :

```text
Failed to write state: cannot import state with lineage "11111111-2222-3333-4444-555555555555" over unrelated state with lineage "cf018339-7f2e-b564-8026-b9621939c826"
```

Une restauration légitime tombe forcément sur le **premier** de ces deux refus,
puisqu'on remet en place un état antérieur. C'est là que `-force` intervient :

```bash
terraform state push -force photo.json
```

Il n'y a **ni confirmation ni question** : l'option passe outre les deux
garde-fous, y compris celui du lineage. Vérifiez donc le lineage **avant** de
forcer, jamais après.

## Ce que devient le `serial` après un push

C'est le détail qui surprend le plus, et il ne se devine pas. Le state restauré
ne reprend **pas** le compteur du state qu'il remplace : il repart de son propre
`serial`, augmenté de un. Poussez de force une photo au `serial` 1 sur un state
au `serial` 15 :

| Fichier | `serial` |
| --- | --- |
| le state courant, avant | 15 |
| la photo poussée | 1 |
| le state courant, après | **2** |

Deux conséquences, opposées. La bonne : un `push` incrémente toujours, donc le
state restauré porte **un `serial` supérieur à celui de la sauvegarde**. Une
copie de fichier posée à la main par-dessus `terraform.tfstate` laisserait, elle,
le `serial` de la sauvegarde à l'identique : le contournement se lit dans le
fichier, longtemps après.

La mauvaise, et elle est sérieuse sur un **backend partagé** : votre state
restauré peut porter un `serial` **très inférieur** à celui que d'autres copies
ont déjà vu. Un collègue dont le cache local connaît le `serial` 15 se retrouve
devant un state à 2, et c'est la porte ouverte à un écrasement en sens inverse.
Après une restauration forcée sur un state partagé, prévenez avant que quelqu'un
ne pousse.

## Restaurer la mauvaise sauvegarde se voit au plan

Une sauvegarde au bon lineage mais **périmée** décrit des attributs qui ne
correspondent plus au réel. Terraform ne s'en plaint pas au `push`, il le dit au
plan suivant :

```text
  # local_file.releve must be replaced
      ~ content = <<-EOT # forces replacement
Plan: 1 to add, 0 to change, 1 to destroy.
```

`terraform plan -detailed-exitcode` rend alors **2**. Le contrôle est
mécanique : après une restauration, un plan qui ne sort pas en **0** signale que
vous avez remis un état qui ne décrit pas l'infrastructure telle qu'elle est.

## Le réflexe qui sauve

Avant toute écriture dans un state, on photographie ce que l'on s'apprête à
remplacer :

```bash
terraform state pull > avant-intervention.json
```

Un `push` ne se rejoue pas : une fois l'état écrasé, la seule chose qui vous
reste est ce que vous avez sauvegardé vous-même. Cette photo coûte une seconde
et vaut le reste de l'intervention.

## À vous de jouer

Vous savez lire un `lineage` et un `serial`, distinguer les deux types de
sauvegardes que Terraform pose, forcer un `push` en connaissance de cause, et
reconnaître au plan une sauvegarde périmée. Le challenge vous remet un projet
dont le state a été amputé, trois sauvegardes candidates dont **une seule** est
restaurable, et une infrastructure parfaitement intacte qu'il ne faut surtout
pas recréer.

```bash
dsoxlab run state-backup-restore-state
dsoxlab check state-backup-restore-state
dsoxlab hint state-backup-restore-state
```

Sous-objectif d'examen visé : **1e** (gérer le state), niveau Associate et
Professional.

Référence : [sauvegarder et restaurer le state](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/sauvegarder-restaurer-state/)
