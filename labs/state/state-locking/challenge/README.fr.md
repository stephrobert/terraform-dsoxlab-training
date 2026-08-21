# 🎯 Challenge : mesurer ce que le verrou bloque, et ce qu'il laisse passer

## ✅ Objectif

Dans `challenge/work`, deux fichiers portent des `???`. À faire :

1. **`main.tf`** : poser le `path` du bloc `backend "local"` sur
   **`etat/projet.tfstate`** (le state doit sortir de la racine), et donner au
   provisioner une commande qui tient l'apply **au moins quinze secondes** ;
2. **`observations.tf`** : mener les mesures, puis remplir les quatre outputs
   avec ce que vous avez **observé**.

Les mesures se mènent depuis un second terminal, pendant qu'un `terraform apply`
tourne dans le premier. Relevez des **codes de retour** (`echo $?`), pas des
messages :

```bash
terraform plan -input=false > /dev/null 2>&1; echo $?
```

Pour `verrou_residuel`, tuez l'apply en cours (`kill -9`), regardez si le fichier
de verrou est encore là, relancez un `plan`, notez son code, puis regardez à
nouveau si le fichier est là.

Pour `backend_s3`, la réponse est dans la page officielle du backend S3 : le nom
de l'argument de verrouillage, sa valeur par défaut, et le statut du
verrouillage par table DynamoDB.

## 🔍 Validation

`dsoxlab check state-state-locking` **refait l'expérience** et compare ses
propres mesures aux vôtres :

- `.terraform/terraform.tfstate` porte `backend.type = local` et
  `backend.config.path = etat/projet.tfstate` ;
- l'apply de remplacement dure bien au moins quinze secondes, sinon aucun verrou
  n'est observable et rien ne peut être mesuré ;
- le verrou capturé porte **sept** champs, un `ID` en UUID, la `Version` de
  votre CLI, et un `Path` qui désigne le state ;
- vos quatre outputs sont confrontés aux relevés du test, geste par geste ;
- plus aucun fichier de verrou ne subsiste à la fin, et
  `plan -detailed-exitcode` rend 0.

Bloqué ? `dsoxlab hint state-state-locking`.
