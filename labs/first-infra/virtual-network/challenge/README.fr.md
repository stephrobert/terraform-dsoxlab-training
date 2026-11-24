# La dépendance que Terraform ne peut pas deviner

## La situation

**Sous-objectif d'examen visé : 2d, les meta-arguments (`depends_on`).**

Le guide crée un réseau NAT et conclut qu'un `depends_on` y serait redondant,
puisque la VM référence déjà l'attribut du réseau. C'est exact : le lab porte
donc sur le cas symétrique, celui où plus aucune référence n'exprime la
dépendance et où Terraform est libre d'agir dans le mauvais ordre.

## Capacité visée

Distinguer une dépendance **implicite**, déduite d'une référence à l'attribut
d'une autre ressource, d'une dépendance **comportementale** invisible dans le
code, et n'employer `depends_on` que dans le second cas : la doc officielle en
fait un recours de dernier ressort.

## D'où part l'apprenant

`challenge/work` contient une configuration incomplète : un réseau virtuel dont
le mode de forwarding et la plage DHCP sont à compléter, une variable qui porte
le **nom** du réseau, et un second bloc qui interroge libvirt avec ce nom pour
produire un rapport sur le disque. Ce second bloc consomme la variable, donc il
ne référence **aucun** attribut du réseau : rien, dans le code, ne dit à
Terraform que le réseau doit exister d'abord. Le répertoire est vierge par
ailleurs : ni `.terraform/`, ni state, ni verrou de dépendances.

Prérequis machine : `libvirtd` actif, appartenance au groupe `libvirt`, accès à
`qemu:///system`, `virsh` sur le PATH, provider `dmacvicar/libvirt` téléchargeable.
Aucune image disque, aucune VM : le lab reste au niveau réseau.

## L'état à atteindre

1. Un réseau NAT existe côté libvirt, avec sa passerelle, son masque, sa plage
   DHCP et le démarrage automatique désactivé.
2. Les outputs exposent le nom du réseau et sa passerelle en **référençant les
   attributs de la ressource**, jamais des chaînes en dur.
3. Le second bloc porte un `depends_on` explicite vers le réseau, parce qu'il
   n'a rien à référencer.
4. Le rapport produit contient ce que seul un réseau **déjà créé** peut fournir.
5. Juste après l'apply, un nouveau plan annonce zéro changement, et après le
   destroy plus rien ne subsiste, ni dans le state ni dans libvirt.

## Comment on le prouve

Tout se lit dans l'état structuré, jamais dans le `.tf` de l'apprenant :

- Le plan en JSON expose la représentation de la configuration : les outputs
  portent des `references` vers le réseau, preuve de la dépendance implicite.
- Ce même JSON montre, pour le second bloc, un `depends_on` contenant l'adresse
  du réseau **et** des expressions dépourvues de toute référence à celui-ci.
  C'est la preuve centrale : la dépendance ne pouvait pas être déduite, elle a
  été déclarée.
- `terraform show -json` après apply confirme le mode de forwarding et la plage
  DHCP enregistrés ; `terraform output -json` renvoie un nom et une passerelle
  cohérents avec eux. Le rapport porte des informations issues de libvirt : le
  second bloc s'est donc exécuté après la création, sinon il aurait échoué.
- Contre-vérification hors Terraform : `virsh net-list --all` liste le réseau,
  et `terraform plan -detailed-exitcode` sort en **0** juste après l'apply.
- Après le destroy, `terraform show -json` ne contient plus aucune ressource et
  `virsh net-list --all` ne connaît plus le réseau : aucun réseau libvirt ne
  survit au lab.

## 🎯 Challenge : la dépendance que Terraform ne peut pas deviner

### Point de départ

`challenge/work` contient une configuration incomplète : un réseau virtuel dont
le **mode de forwarding** et la **plage DHCP** sont à compléter, et un second
bloc qui produit un rapport en interrogeant libvirt.

**Prérequis** : `libvirt` joignable en `qemu:///system`, votre utilisateur dans
le groupe `libvirt`, `virsh` sur le `PATH`. Aucune image disque, aucune VM : le
lab reste au niveau réseau.

### ✅ Objectif

1. **Le mode de forwarding** du réseau : un mode qui donne un accès sortant sans
   exposer les machines.
2. **La plage DHCP**, de `.100` à `.200`.
3. **Le méta-argument** qui manque au second bloc.
4. **Deux sorties**, qui référencent les attributs de la ressource.

### 🧭 Regardez bien le second bloc

Il interroge libvirt **avec le nom du réseau**, pris dans la variable. Il lit
`var.nom_du_reseau`, pas `libvirt_network.lab.name`.

La différence est invisible à la lecture et décisive à l'exécution : Terraform
construit son graphe à partir des **références qu'il trouve dans les
expressions**. Ici il n'en trouve aucune. Les deux blocs sont donc indépendants
à ses yeux, et il est **libre de lancer le rapport en premier**.

Il le fait. Et quand il le fait, `virsh net-dumpxml` échoue sur un réseau qui
n'existe pas encore, la redirection crée un fichier **vide**, et Terraform
annonce `Apply complete!`. Rien ne le signale. C'est le genre de défaut qui
passe la revue et casse en production une fois sur deux.

<Aside type="caution" title="La règle habituelle dit l'inverse">
Neuf fois sur dix, un `depends_on` écrit à la main signale une **référence
manquante** : il suffit de référencer l'attribut pour que l'arête apparaisse, et
le méta-argument devient un pansement. Ce lab porte sur la dixième fois, celle
où il n'y a **rien** à référencer.
</Aside>

### 🔍 Validation

```bash
dsoxlab check first-infra-virtual-network
```

Six tests. La configuration est lue dans le plan converti en JSON, où Terraform
expose **ce qu'il a compris** : les `references` de chaque output et le
`depends_on` de chaque ressource. Un test vérifie que le `depends_on` est bien
la **seule** chose qui relie les deux blocs — posé à côté d'une référence, il ne
prouverait rien. Le réseau est détruit en sortie, quoi qu'il arrive.
