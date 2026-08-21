# Scénario : l'inventaire Ansible est une ressource, pas un effet de bord

**Sous-objectif d'examen visé : 2e (déclarer et consommer variables et outputs en types complexes), avec appui sur 1e (lire le state pour prouver ce qui est réellement géré).**

Terraform provisionne, Ansible configure, et l'inventaire est leur seul point de
contact. Le lab impose la seule façon de le fabriquer qui survive au plan suivant :
une ressource gérée, dérivée du state, et non un fichier posé au passage.

## Capacité visée

Produire depuis Terraform un inventaire consommable par un outil de configuration,
dont chaque valeur dérive du state, puis démontrer que cet artefact est suivi :
recréé s'il disparaît, mis à jour si une valeur change, supprimé au `destroy`.

Le piège est là. La doc officielle range les provisioners `local-exec` et
`remote-exec` au rang de dernier recours : Terraform ne sait pas modéliser leur
comportement, ils ne laissent aucune ressource à inspecter dans le state et ne
rejouent qu'à la création ou à la destruction de leur porteuse. L'inventaire qu'ils
produisent est juste le jour de l'apply, faux le lendemain.

## D'où part l'apprenant

`challenge/work` contient une configuration incomplète, sans cloud ni hyperviseur :
le parc est simulé par des ressources dont certains attributs ne sont connus qu'après
création, comme une adresse allouée par un ordonnanceur. Une variable de type complexe
décrit les serveurs (nom logique, rôle, index réseau), un CIDR de base est fourni,
aucune adresse n'est écrite en dur : une valeur devinable ne prouverait rien. Les
`???` portent sur le type de la variable, le calcul des adresses par fonction HCL, la
ressource du provider `local` qui écrit l'inventaire, et l'output qui l'expose. Le
fichier d'inventaire, lui, est absent au départ.

## L'état à atteindre

1. La variable du parc est déclarée en type structuré explicite, jamais en `any`.
2. Les adresses sont calculées depuis le CIDR de base et l'index de chaque serveur,
   par fonction HCL, jamais recopiées.
3. Une ressource gérée du provider `local` écrit l'inventaire attendu par Ansible,
   groupes et variables d'hôte compris, sérialisé par fonction et non par concaténation.
4. Un output expose le même inventaire sous forme structurée.
5. Chaque valeur du fichier généré est identique à celle du state, y compris un
   attribut calculé impossible à écrire de tête.
6. Juste après l'apply, un nouveau plan annonce aucun changement.
7. Le fichier supprimé à la main, le plan suivant annonce sa recréation ; une valeur
   du parc modifiée, il annonce sa mise à jour.
8. Après le `destroy`, le fichier d'inventaire a disparu du disque.

## Comment on le prouve

Tout se lit dans l'état structuré et dans l'artefact produit, jamais dans le `.tf` :

- `terraform output -json` rend l'inventaire sous forme d'objet, comparé valeur par
  valeur au fichier généré puis désérialisé : tout écart signe une saisie manuelle.
- `terraform show -json` expose les attributs calculés des serveurs simulés ; ceux que
  porte le fichier doivent être ceux du state, ce qui interdit la valeur inventée.
- `terraform state list` contient la ressource qui produit l'inventaire, là où un
  provisioner ne laisserait aucune adresse à lister.
- `terraform plan -detailed-exitcode` sort en 0 juste après l'apply, en 2 après
  suppression du fichier, en 2 après modification du parc : un provisioner resterait
  en 0 dans les deux cas.
- Après `terraform destroy`, le fichier n'est plus sur le disque et le state est vide.
