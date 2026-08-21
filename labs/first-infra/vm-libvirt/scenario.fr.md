# Scénario : mise à jour en place ou remplacement, le lire dans le plan

**Sous-objectif d'examen visé : 1b `plan`.**

Sur une machine virtuelle, certains attributs se modifient en place et d'autres
détruisent puis recréent la machine. Le plan le dit avant l'apply, à condition de
savoir où regarder.

## Capacité visée

Déclarer une VM libvirt minimale, puis, face à une modification demandée,
prédire **avant tout apply** si Terraform fera une mise à jour en place ou un
remplacement, et le prouver par le champ des actions du plan en JSON plutôt que
par la sortie humaine ou par une intuition sur l'attribut touché.

## D'où part l'apprenant

Ce lab provisionne de vraies ressources locales : il suppose `libvirtd` actif sur
`qemu:///system`, un pool `default` utilisable, et une image cloud déjà
téléchargée. Aucun cloud, aucun coût, une seule VM.

`challenge/work` contient une configuration trouée pour **une seule VM
minimale** : le volume qcow2 dérivé de l'image locale, et le domaine qui le
référence, avec une mémoire réduite et un seul vCPU sur le réseau `default`. Les
`???` portent sur la contrainte de version du provider `dmacvicar/libvirt`, sur
les attributs du domaine, et sur les outputs exposant le nom et l'identifiant de
la machine. Le répertoire est vierge : ni `.terraform/`, ni verrou, ni state.

## L'état à atteindre

1. Le provider est installé sous contrainte de version et le fichier de
   verrouillage le fige.
2. L'apply crée exactement les ressources attendues, un volume et un domaine, et
   la VM tourne.
3. Un plan relancé juste après n'annonce **aucun changement**.
4. Une première modification, portant sur les ressources allouées, produit un
   plan que l'apprenant qualifie **avant** de l'appliquer, actions à l'appui.
5. Une seconde modification, portant sur l'identité du domaine, produit un plan
   dont les actions diffèrent de la première : ce n'est plus le même verbe, et
   l'apprenant l'annonce là aussi avant d'appliquer.
6. Après ce second apply, l'identifiant du domaine relevé dans le state a
   **changé**, ce que le premier apply n'avait pas provoqué.
7. Le `destroy` est propre : plus rien dans le state, aucune VM du lab ne survit
   sur l'hôte, aucun volume du lab ne reste dans le pool.

## Comment on le prouve

Rien n'est vérifié en relisant les fichiers `.tf` de l'apprenant.

- Le plan est enregistré avec `terraform plan -out`, puis relu en JSON. Dans
  `resource_changes`, `change.actions` tranche sans ambiguïté : `["update"]`
  pour une mise à jour en place, `["delete","create"]` pour un remplacement,
  auquel cas `replace_paths` et `action_reason` sont relevés au même endroit.
  C'est cette valeur qui est comparée, jamais un texte affiché.
- `terraform show -json` donne l'état géré après chaque apply : comparer
  l'identifiant du domaine avant et après confirme l'opération réellement subie.
- `terraform plan -detailed-exitcode` juge la convergence : 0 quand la
  configuration est stable, 2 tant qu'un changement reste en attente.
- Contre-vérification hors Terraform, jamais source de vérité : `virsh list
  --all` montre la VM entre les deux apply puis plus rien après le `destroy`.
