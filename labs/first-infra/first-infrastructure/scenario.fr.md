# Scénario : première infrastructure, le cycle complet

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
