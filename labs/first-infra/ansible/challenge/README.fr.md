# L'inventaire Ansible est une ressource, pas un effet de bord

## La situation

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

## 🎯 Challenge : produire un inventaire Ansible depuis le state

### Point de départ

`challenge/work` contient une configuration incomplète. **Aucun cloud, aucun
hyperviseur** : le parc est simulé par des ressources dont certains attributs ne
sont connus **qu'après création**, comme une adresse allouée par un
ordonnanceur.

C'est délibéré : une valeur devinable ne prouverait rien.

### ✅ Objectif

1. **Le type du parc**, en structure explicite. Jamais `any`.
2. **Les adresses**, calculées depuis le CIDR de base et l'index de chaque
   serveur, **par une fonction HCL**.
3. **La ressource** du provider `local` qui écrit `inventaire.json`, sérialisé
   **par une fonction**.
4. **L'output**, qui expose l'inventaire sous forme **structurée**.

### 🧭 Quatre choix qui séparent un pont fiable d'un pont qui tient debout

**Un type explicite refuse au plan.** `map(object({ role = string, index =
number }))` rejette une entrée sans `index` **avant tout appel de provider**.
Avec `any`, la même faute passe le plan et casse plus loin, sur un message qui
ne nomme ni la variable ni l'entrée fautive.

**Une adresse se calcule.** `cidrhost(var.cidr_de_base, serveur.index)` suit le
réseau. Recopiée à la main, elle est juste aujourd'hui et fausse au premier
changement, **sans que rien ne le signale**.

**`jsonencode` plutôt qu'une concaténation.** Une chaîne construite à la main
produit du JSON *presque* valide : une virgule en trop, un guillemet oublié dans
un nom, et Ansible rend une erreur de parsing qui ne dit pas où.

**Un fichier géré disparaît avec le parc.** Un inventaire qui survit à la
destruction pointe vers des machines qui n'existent plus. Ansible s'y
connectera, échouera, et le message parlera de réseau.

### 🔍 Validation

```bash
dsoxlab check first-infra-ansible
```

Sept tests. Les adresses ne sont pas comparées à une liste écrite dans le test :
elles sont **recalculées** depuis le CIDR, deux calculs indépendants valant
mieux qu'une constante. Et le fichier doit porter les identifiants **tirés à la
création** : les adresses se devinent, ceux-là non.
