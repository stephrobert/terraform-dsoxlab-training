# Scénario : détruire sans perdre le state

**Sous-objectif d'examen visé : 1d (`terraform destroy`), avec appui sur 1e (inspecter le state).**

Détruire n'est pas un geste unique : destroy complet, destroy ciblé, refus opposé
par `prevent_destroy`, ressource retirée du code qui disparaît sans qu'on l'ait
demandé. Et un destroy réussi vide le state, il ne supprime pas le fichier.

## Capacité visée

Piloter une destruction : la **bloquer** par un garde-fou, la **cibler** sur une
partie du graphe, la **provoquer** en retirant du code, puis prouver sur de
l'état structuré ce qui a disparu et ce qui subsiste. Savoir qu'un plan de
destruction se lit avant de s'exécuter, et que `prevent_destroy` ne protège plus
rien dès que le bloc de ressource quitte la configuration.

## D'où part l'apprenant

`challenge/work` contient une configuration bâtie sur les providers `random`,
`local` et `null` : aucun cloud, aucune VM, aucun appel réseau, tout est
déterministe et rejouable. Trois ressources forment une chaîne de dépendances
explicite : un `random_pet` donne un suffixe, un `local_file` écrit un
inventaire qui référence ce suffixe, un `null_resource` déclare un `triggers`
calculé depuis le chemin du fichier. Une quatrième ressource, indépendante des
trois autres, sert de témoin. Le répertoire est vierge : ni `.terraform/`, ni
state, et un bloc `lifecycle` incomplet porte des `???` sur la ressource à
protéger.

## L'état à atteindre

1. La configuration est initialisée puis appliquée : les quatre ressources
   existent dans le state.
2. Le `local_file` est protégé par un `lifecycle { prevent_destroy = true }` :
   un `terraform destroy` complet **échoue** sans rien détruire, code de retour
   conservé dans `artefacts/rc-prevent-destroy.txt`.
3. Un plan de destruction exporté en JSON sous `artefacts/plan-destroy.json`
   annonce la suppression des quatre ressources, sans en détruire aucune.
4. Une fois la protection levée, un **destroy ciblé** ne retire que le
   `null_resource` : les trois autres ressources restent gérées.
5. La ressource témoin est **retirée du code**, puis un `apply` est lancé :
   Terraform la détruit parce qu'elle n'est plus déclarée.
6. Un `destroy` complet vide le state du reste, et `terraform.tfstate` **existe
   toujours** sur le disque, sans plus aucune ressource gérée.

## Comment on le prouve

Aucun test ne relit le `.tf` de l'apprenant, aucun ne parse une sortie humaine.

- Le garde-fou : **code de retour non nul** relevé dans
  `artefacts/rc-prevent-destroy.txt`, croisé avec un `terraform show -json` qui
  montre les quatre ressources toujours gérées.
- Le **plan complet** : dans `artefacts/plan-destroy.json`, les quatre adresses
  portent l'action `delete`. Ce sont les adresses qui sont comptées, et non la
  seule existence du fichier : un plan pris avant la levée de la protection
  échoue, écrit quand même son fichier, et n'y met que trois ressources.
- Le **ciblage** et le **retrait du code** : par les adresses restantes dans
  `terraform show -json`, celle du `null_resource` puis celle du témoin.
- L'**état final**, sur deux points distincts : le fichier de state est présent
  et reste un JSON valide avec ses champs de version et de lignée, et
  `terraform show -json` n'expose plus rien sous `values.root_module`. Confondre
  les deux est le piège du lab.
