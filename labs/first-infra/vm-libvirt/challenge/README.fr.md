# 🎯 Challenge : mise à jour en place ou remplacement

## Point de départ

`challenge/work` contient une configuration trouée pour **une seule VM
minimale** : un disque qcow2 en copie sur écriture depuis une image cloud, et le
domaine qui le référence.

**Prérequis** : `libvirt` joignable en `qemu:///system`, le pool `default` et le
réseau `default` utilisables, et l'image cloud présente :

```bash
mkdir -p /var/tmp/dsoxlab-images && curl -fsSL \
  -o /var/tmp/dsoxlab-images/noble-server-cloudimg-amd64.img \
  https://cloud-images.ubuntu.com/noble/current/noble-server-cloudimg-amd64.img
```

L'image n'est jamais modifiée : le disque de la VM ne porte que les blocs qui
changent. C'est ce qui permet de recréer une machine en une seconde plutôt que
de recopier 600 Mio.

## ✅ Objectif

1. **La contrainte de provider**, qui doit désigner sans ambiguïté la série dont
   le code utilise le schéma.
2. **Les attributs du domaine** : le nom, le type d'hyperviseur, la mémoire et
   son unité, le nombre de vCPU, et le fait que la machine doit **tourner**.
3. **Deux sorties** : le nom du domaine et son **identifiant**.

Puis, face à deux modifications, **qualifiez le plan avant de l'appliquer** :
une sur les ressources allouées, une sur l'identité de la machine.

## 🧭 Ce que le lab vous fait constater

- **Mémoire et vCPU se modifient en place.** libvirt sait redéfinir un domaine
  sans le détruire : le plan annonce `["update"]`.
- **Le nom force un remplacement.** Il *est* l'identité du domaine : le changer
  ne modifie pas la machine, il en fabrique une autre. Le plan annonce
  `["delete", "create"]` et `replace_paths = [["name"]]`.
- **L'identifiant le prouve après coup.** libvirt l'attribue à la création : une
  machine modifiée garde le sien, une machine remplacée en reçoit un autre.
- **`running` ne prouve pas qu'une VM a booté.** Une machine sans disque
  bootable est `running` elle aussi. Ce qui les distingue est le **temps CPU** :
  0,3 s dans un cas, plusieurs secondes dans l'autre.

## 🔍 Validation

```bash
dsoxlab check first-infra-vm-libvirt
```

Sept tests. Les cinquième et sixième lisent des **plans**, donc des prédictions.
Le septième les **applique** et compare l'identifiant du domaine : c'est la
seule façon de savoir si l'outil a tenu parole. La VM et son disque sont
détruits en sortie, quoi qu'il arrive.
