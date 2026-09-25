# `sensitive` protège l'écran, pas le state

L'objectif 6 du Professional est évalué **en QCM**, et ne demande aucun compte.
Mais ce qu'il enseigne se mesure, et ce lab le mesure sur un vrai provider face à
un émulateur local.

Il se referme sur une supposition que presque tout le monde fait une fois.

## La mesure

Une variable marquée `sensitive`, écrite dans une étiquette de ressource. Le
2026-09-25, sur Terraform 1.16.1 :

```console
$ terraform show | grep Jeton
    "Jeton" = (sensitive value)

$ grep -c 'svc-7f3a91c4e2b8-prod' terraform.tfstate
2
```

L'annotation a fait son travail : Terraform n'a jamais affiché la valeur. Et le
state la porte en clair, deux fois, dans `tags` et dans `tags_all`. Un plan
enregistré la porte également.

`sensitive` agit sur la **sortie**, pas sur le stockage. Un state se lit, se
sauvegarde, se partage, et se committe parfois par erreur : tout ce qui y atterrit
est divulgué.

## Ce qu'on enregistre à la place d'un secret

Une **empreinte**, chaque fois qu'il s'agit de *vérifier* et non de *rejouer* :

```hcl
tags = {
  Empreinte = sha256(var.jeton_de_service)
}
```

Elle prouve qu'un jeton présenté est bien celui qu'on attend, et elle ne permet
pas de le retrouver. Exactement le raisonnement qui fait qu'on ne stocke jamais
un mot de passe.

## Où vivent les identifiants

Pas dans la configuration. HCP Terraform les pose dans l'**environnement du
run**, juste avant le plan ou l'apply, et le provider AWS y lit
`AWS_ACCESS_KEY_ID` et `AWS_SECRET_ACCESS_KEY` quand la configuration ne lui
donne rien.

C'est ce qui rend une même configuration utilisable partout : avec les clés
statiques d'un workspace, avec des identifiants dynamiques, ou avec un rôle
assumé sur un poste. Le fichier est écrit pour **recevoir** des identifiants, pas
pour en contenir.

Attention toutefois, et cela se mesure : sans identifiant **nulle part**, le
provider AWS répond `No valid credential sources found` et ne plane même pas.
Retirer les clés est la moitié du travail ; l'environnement doit les fournir.

## Les identifiants dynamiques, en sept temps

Les identifiants statiques sont un risque « même si vous les tournez
régulièrement ». Les identifiants dynamiques les remplacent par des identifiants
forgés à chaque run :

1. HCP Terraform génère un **workload identity token**, conforme OIDC, portant
   l'organisation, le workspace et l'**étape du run** ;
2. au démarrage d'un plan ou d'un apply, il l'envoie à la plateforme cloud ;
3. la plateforme le vérifie avec la **clé publique de signature de HCP
   Terraform** ;
4. si la vérification réussit, elle renvoie des **identifiants temporaires
   frais** ;
5. HCP Terraform les pose dans l'environnement du run, pour le provider ;
6. le plan ou l'apply se déroule ;
7. à la fin, **l'environnement est détruit et les identifiants sont jetés**.

D'où la propriété à retenir : un identifiant qui ne survit pas à son run n'a pas
besoin d'être tourné. La mise en place tient en trois étapes, une relation de
confiance, des rôles et politiques sur la plateforme, et des variables
d'environnement sur le workspace, et les agents auto-hébergés doivent être en
**v1.7.0** ou plus récent.

## À vous

```bash
dsoxlab run hcp-terraform-shared-credentials
dsoxlab check hcp-terraform-shared-credentials
dsoxlab hint hcp-terraform-shared-credentials
```

Huit tests. Ils appliquent votre configuration dans un environnement de run qu'ils
construisent eux-mêmes, expurgé de tout `AWS_*` du poste et sans `~/.aws`, puis
lisent le state et balaient le fichier entier à la recherche du jeton.

Sous-objectif d'examen visé : **6c**.

Référence : [les identifiants dynamiques de provider](https://developer.hashicorp.com/terraform/cloud-docs/workspaces/dynamic-provider-credentials)
