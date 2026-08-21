# Le verrou du state : où le chercher, et comment savoir s'il est vivant

Avant toute opération susceptible d'écrire le state, Terraform pose un
**verrou**. Tant qu'il est tenu, une autre opération susceptible d'écrire est
rejetée. C'est ce qui empêche deux `apply` simultanés de se marcher dessus. Ce
tutoriel montre comment observer ce mécanisme au lieu de le croire sur parole ;
le challenge vous fera relever vos propres mesures.

## Rendre le verrou observable

Un verrou dure le temps de l'opération. Sur une configuration triviale, l'apply
se termine en une fraction de seconde et il n'y a rien à voir. Pour l'observer,
il faut une ressource qui prenne du temps :

```hcl
resource "terraform_data" "attente" {
  input = "demo"

  provisioner "local-exec" {
    command = "sleep 30"
  }
}
```

`terraform_data` est **intégré à Terraform** : aucun provider à télécharger. Le
provisioner `local-exec` n'est utilisé ici que comme minuteur d'observation, ce
n'est pas un usage recommandé pour configurer un système.

Pendant que cet apply tourne dans un premier terminal, un second terminal permet
de mener les observations.

## Où le fichier de verrou atterrit

Avec le backend local, le verrou est un fichier posé **à côté du state**, pas à
un emplacement fixe. Son nom se **dérive** du chemin du state : le nom du fichier
de state, préfixé d'un point, suffixé de `.lock.info`. Avec le `path` par défaut
(`terraform.tfstate` à la racine), cela donne `.terraform.tfstate.lock.info` à la
racine, d'où la confusion fréquente. Déplacez le state, le verrou suit :

```hcl
terraform {
  backend "local" {
    path = "stockage/infra.tfstate"
  }
}
```

Le verrou s'écrit alors en `stockage/.infra.tfstate.lock.info`. Son contenu est
un objet JSON dont le champ `Path` désigne le **state verrouillé**, pas le
fichier de verrou lui même. Pour le trouver sans le deviner :

```bash
find . -name '*.lock.info'
```

## Relever un code de retour, pas un message

Un message d'erreur se reformule d'une version à l'autre ; le **code de retour**,
lui, se compare. C'est la seule mesure fiable pour établir ce qui passe et ce qui
est rejeté :

```bash
terraform plan -input=false > /dev/null 2>&1; echo $?
```

`0` signifie que la commande a abouti, `1` qu'elle a été rejetée. En lançant
chaque geste de cette façon pendant qu'un verrou est tenu, vous obtenez un
tableau de faits et non d'impressions. Deux points méritent l'attention : toutes
les commandes ne prennent pas de verrou, et l'option `-lock=false` n'existe pas
sur toutes.

## L'attente plutôt que le rejet

Par défaut, une commande refusée par un verrou échoue **immédiatement** :
`-lock-timeout` vaut `0s`. En intégration continue, deux exécutions qui se
suivent de près se rejettent alors l'une l'autre pour quelques secondes de
recouvrement. Une durée de réessai suffit :

```bash
terraform apply -lock-timeout=5m
```

C'est le bon réflexe, très loin devant `-lock=false`, qui ne fait pas attendre :
il supprime la protection.

## Verrou tenu et fichier résiduel

Le backend local, dit la documentation, verrouille le state « using system
APIs ». Le verrou réel est donc un **verrou système** posé par le processus, et
le noyau le libère à la mort de ce processus, quelle qu'en soit la cause. Le
fichier `.lock.info` n'est que la carte de visite de ce verrou : il dit qui
détient quoi, il ne détient rien lui même.

La conséquence est contre-intuitive et se vérifie en une minute. Tuez un apply en
cours, regardez si le fichier est encore là, relancez un `plan` et notez son code
de retour, puis regardez à nouveau si le fichier est là. C'est exactement la
mesure que le challenge vous demande.

## Ce qui active le verrouillage sur un backend distant

Sur un backend distant, le verrouillage n'est **pas** systématique : il dépend du
backend et de sa configuration. Le backend **S3** le décrit comme une
fonctionnalité **opt-in**, gouvernée par un argument dédié qui vaut `false` par
défaut. Une configuration S3 qui ne le pose pas n'a aucun verrou, même sur une
version récente de Terraform. L'ancien mécanisme fondé sur une table **DynamoDB**
existe toujours mais ne doit plus servir de référence. La page officielle du
backend S3 nomme cet argument et donne son défaut.

## À vous de jouer

Vous savez rendre un verrou observable, le trouver sur le disque, lire son champ
`Path`, relever un code de retour plutôt qu'un message, et distinguer un verrou
système d'un fichier résiduel. Le challenge vous fait mener ces mesures et
consigner vos constats : les tests refont l'expérience de leur côté, puis
comparent.

```bash
dsoxlab run state-state-locking
dsoxlab check state-state-locking
dsoxlab hint state-state-locking
```

Sous-objectif d'examen visé : **3b** (verrouillage du state), niveau Professional.

Référence : [Verrouiller le state Terraform](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/state/verrouillage-state/)
