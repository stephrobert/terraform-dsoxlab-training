# Scénario : prouver ce que le verrou du state bloque vraiment

**Sous-objectif d'examen visé : 3b, gérer le state distant, son verrouillage et sa reprise après incident.**

On croit quatre choses fausses sur le verrouillage : que seul l'`apply` est
concerné, qu'il est actif par défaut sur tout backend qui le supporte, que le
fichier de verrou vit toujours à la racine du projet, et qu'un fichier resté sur
le disque après un plantage bloque la suite. Ce lab les met à l'épreuve plutôt
que de les répéter.

## Capacité visée

Établir expérimentalement le périmètre exact du verrouillage sur un backend
local (ce qu'il rejette, ce qu'il laisse passer, où il s'écrit, comment il se
libère), puis énoncer la configuration qui l'active sur un backend S3. L'enjeu
n'est pas de taper `terraform force-unlock`, c'est de savoir si le verrou qu'on
a sous les yeux est vivant ou n'est qu'un fichier résiduel : la mauvaise réponse
fait supprimer un verrou pendant qu'un collègue applique.

## D'où part l'apprenant

`challenge/work` contient deux fichiers incomplets. Dans `main.tf`, le `path` du
bloc `backend "local"` est troué par `???`, et la commande du provisioner
`local-exec` d'une ressource `terraform_data` l'est aussi. Dans
`observations.tf`, quatre outputs attendent les constats de l'apprenant. Aucun
`.terraform/`, aucun state. Lab de type `shell`, aucun provider externe :
`terraform_data` est intégré à Terraform, le lab se joue hors ligne, sans VM ni
compte cloud. Rendre l'apply assez lent pour qu'un verrou soit observable
conditionne toute la suite.

## L'état à atteindre

1. Le backend local pointe sur un state hors racine, `etat/projet.tfstate`, le
   répertoire est initialisé, la configuration appliquée et convergée, et son
   apply dure au moins quinze secondes.
2. L'output `fichier_verrou` donne le chemin réel du fichier de verrou, relatif
   à la racine du projet.
3. L'output `codes_pendant_verrou` donne le code de retour observé pour six
   gestes tentés pendant qu'un verrou est tenu : `plan`, `apply`,
   `plan -lock=false`, `force-unlock`, `state list` et `show -json`.
4. L'output `verrou_residuel` donne le code de retour d'un `plan` relancé alors
   qu'un fichier de verrou traîne après un arrêt brutal, et dit si ce fichier
   est encore là après ce `plan`.
5. L'output `backend_s3` nomme l'argument qui active le verrouillage natif S3,
   dit s'il est actif sans rien configurer, et donne le statut du verrouillage
   par table DynamoDB.
6. Après la fin de l'apply, plus aucun fichier de verrou ne subsiste.

## Comment on le prouve

Les tests s'exécutent dans `challenge/work`, n'ouvrent jamais les `.tf` de
l'apprenant et ne lisent aucune sortie destinée à un humain.

- Le backend est lu dans `.terraform/terraform.tfstate`, l'artefact machine
  produit par `init` : `backend.type` vaut `local` et `backend.config.path` le
  chemin attendu. `terraform show -json` décrit la ressource lente en
  `mode: managed` et `terraform plan -detailed-exitcode` renvoie 0.
- Les tests refont l'expérience : ils lancent un apply en arrière plan, attendent
  l'apparition du verrou, relèvent eux mêmes les codes de retour des points 3 et
  4, tuent un apply par `kill -9` pour fabriquer un fichier résiduel, puis
  comparent leurs propres mesures aux outputs déclarés. Rien n'est écrit en dur
  côté résultat attendu.
- Le verrou capturé est confronté à sa forme officielle : sept clés exactement,
  `Operation` valant `OperationTypeApply`, `ID` au format UUID, `Version` égale
  au `terraform_version` de `terraform version -json`, `Path` égal au chemin du
  state configuré, et non à celui du fichier de verrou.
- Quatre idées reçues tombent : le `plan` concurrent sort en erreur, le
  `force-unlock` local échoue quoi qu'il arrive, le `plan` relancé après un
  arrêt brutal réussit malgré le fichier résiduel, et ce fichier est effacé par
  Terraform lui même.
- Seul `backend_s3` n'est pas mesurable hors ligne : il est comparé à la
  documentation officielle du backend S3, `use_lockfile`, `false` par défaut,
  verrouillage par table DynamoDB déprécié.
- Aucune de ces preuves ne passe sur un répertoire vide, ni sur un répertoire
  dont l'apply serait trop rapide pour qu'un verrou soit observable.
