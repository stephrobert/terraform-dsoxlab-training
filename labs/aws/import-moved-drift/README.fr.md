# Import, moved et dérive : les trois pièges qu'un tutoriel ne montre jamais

Reprendre une ressource existante, la renommer, encaisser un changement fait à
la main : trois gestes courants, et trois façons de se tromper **sans qu'aucun
message ne le dise**. C'est ce qui les rend coûteux : ils ne cassent pas, ils
mentent.

Le lab se joue sur **Floci**, un émulateur AWS local : aucun compte, aucune
facture.

## Un import n'est pas fini quand la ressource est dans le state

C'est le premier contresens. Le critère de réussite d'un import n'est pas « la
ressource apparaît dans `terraform state list` », c'est :

```console
$ terraform plan -detailed-exitcode
No changes.
$ echo $?
0
```

Tant qu'un plan ordinaire propose quelque chose, l'import n'est pas fini : votre
code décrit autre chose que l'objet réel, et le prochain `apply` modifiera cet
objet.

Le piège est amplifié par `-generate-config-out`, qui rend service et produit
aussi des arguments que l'API renvoie et que la configuration n'a pas à porter.
Les retirer fait partie du travail.

Et avant tout cela : **personne ne vous tend l'identifiant**. Le retrouver est
la première étape.

```bash
aws --endpoint-url http://localhost:14566 ec2 describe-instances \
    --filters 'Name=tag:Name,Values=legacy-billing-api' \
              'Name=instance-state-name,Values=running' \
    --query 'Reservations[].Instances[].InstanceId' --output text
```

## Un `plan` seul n'écrit rien dans le state

Un bloc `moved` change l'adresse logique d'une ressource sans toucher à l'objet
réel :

```hcl
moved {
  from = aws_instance.legacy
  to   = aws_instance.billing_api
}
```

On le planifie, on voit le renommage annoncé, et on passe à autre chose. Mais
**un plan n'écrit rien** : tant qu'il n'est pas appliqué, le state porte encore
l'ancienne adresse.

Et le bloc **reste en place** après coup. Le supprimer est un changement cassant
pour quiconque part encore de l'ancienne adresse, par exemple une branche non
fusionnée ou un state plus ancien.

## Un `moved` dont le `from` est faux est ignoré en silence

Celui-là est le pire du lot. Si l'adresse `from` ne correspond à rien, Terraform
**ne dit rien** : il ne trouve rien à déplacer, poursuit, et **crée** la
ressource cible.

Résultat : l'objet réel se retrouve **dupliqué**, une fois hors du state et une
fois dedans. Aucune erreur, aucun avertissement, et un plan qui semble normal.

C'est pourquoi le test du lab ne se contente pas de voir la bonne adresse : il
copie votre répertoire, remet l'ancienne adresse dans le state copié, et exige
que le plan porte une entrée `previous_address` en `no-op`. Un `moved` supprimé
ou mal écrit produirait un `create` à cet endroit.

## Écraser une dérive est un réflexe, pas une décision

Quelqu'un a changé un tag à la main. Le plan propose de le remettre. Le réflexe
est d'appliquer, parce que « le code fait foi ».

Mais une dérive est une **information** : quelqu'un a fait quelque chose, pour
une raison qu'on ignore. L'écraser efface à la fois le changement et la raison,
et le collègue qui l'avait fait ne saura jamais pourquoi son tag a disparu.

Accepter la dérive, c'est aligner le **code sur la réalité**. Deux codes de
retour tombent alors ensemble, et il faut les deux :

```console
$ terraform plan -detailed-exitcode                 # 0 : le réel colle au code
$ terraform plan -refresh-only -detailed-exitcode   # 0 : le state colle au réel
```

Le premier seul ne suffit pas : il peut sortir en 0 sur un state périmé.

## À vous de jouer

```bash
dsoxlab run aws-import-moved-drift
dsoxlab check aws-import-moved-drift
dsoxlab hint aws-import-moved-drift
```

Six tests. Le `moved` est prouvé **sans ouvrir un `.tf`**, et une contre-mesure
vérifie côté Floci qu'aucune instance supplémentaire n'existe : ni destroy, ni
create.

Sous-objectif d'examen visé : **1e**.

Référence : [import, moved et dérive](https://blog.stephane-robert.info/docs/infra-as-code/provisionnement/terraform/aws/import-moved-drift/)
