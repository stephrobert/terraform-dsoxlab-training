# 🎯 Challenge : la dépendance que Terraform ne peut pas deviner

## Point de départ

`challenge/work` contient une configuration incomplète : un réseau virtuel dont
le **mode de forwarding** et la **plage DHCP** sont à compléter, et un second
bloc qui produit un rapport en interrogeant libvirt.

**Prérequis** : `libvirt` joignable en `qemu:///system`, votre utilisateur dans
le groupe `libvirt`, `virsh` sur le `PATH`. Aucune image disque, aucune VM : le
lab reste au niveau réseau.

## ✅ Objectif

1. **Le mode de forwarding** du réseau : un mode qui donne un accès sortant sans
   exposer les machines.
2. **La plage DHCP**, de `.100` à `.200`.
3. **Le méta-argument** qui manque au second bloc.
4. **Deux sorties**, qui référencent les attributs de la ressource.

## 🧭 Regardez bien le second bloc

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

## 🔍 Validation

```bash
dsoxlab check first-infra-virtual-network
```

Six tests. La configuration est lue dans le plan converti en JSON, où Terraform
expose **ce qu'il a compris** : les `references` de chaque output et le
`depends_on` de chaque ressource. Un test vérifie que le `depends_on` est bien
la **seule** chose qui relie les deux blocs — posé à côté d'une référence, il ne
prouverait rien. Le réseau est détruit en sortie, quoi qu'il arrive.
