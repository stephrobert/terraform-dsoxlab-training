# Détruire sans perdre le state

## La situation

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

## 🎯 Challenge : détruire proprement

### Point de départ

`challenge/work` contient quatre ressources. Trois forment une chaîne de
dépendances, la quatrième est un **témoin** indépendant. Le bloc `lifecycle` du
`local_file` est troué.

Aucun cloud, aucune VM, aucun appel réseau : tout est déterministe et rejouable.

### ✅ Objectif, dans cet ordre

1. **Protégez** le `local_file` par le méta-argument qui interdit sa
   destruction, puis appliquez.
2. **Lancez un `destroy` global** : il doit **échouer**. Conservez son code de
   retour dans `artefacts/rc-prevent-destroy.txt`.
3. **Levez la protection**, puis exportez un plan de destruction en JSON dans
   `artefacts/plan-destroy.json` — sans rien détruire.
4. **Détruisez de façon ciblée** le seul `null_resource`.
5. **Retirez le témoin du code**, puis appliquez : Terraform le détruit parce
   qu'il n'est plus déclaré.
6. **Détruisez le reste**.

### 🧭 Les quatre façons de détruire, et ce qui les distingue

| Geste | Ce qu'il fait |
|---|---|
| `destroy` global | tout, sauf ce qu'un garde-fou **refuse** |
| `destroy -target` | **uniquement** ce qu'on nomme |
| retirer du code | détruit au prochain `apply`, **sans aucun `destroy`** |
| `destroy` complet | vide le state, **sans supprimer son fichier** |

<Aside type="caution" title="Un plan qui échoue écrit quand même un fichier">
`terraform plan -destroy` sur une configuration protégée sort en **code 1** et
produit **quand même** le fichier demandé par `-out`. Ce plan est
**incomplet** : trois ressources sur quatre. On le relit, on le croit, et il
ment par omission. C'est pourquoi l'étape 3 vient **après** la levée de la
protection.
</Aside>

Et un dernier réflexe à perdre : **ne supprimez pas `terraform.tfstate`** après
un `destroy`. Le fichier porte le `lineage` du projet et son `serial` ; le
supprimer fait repartir Terraform de zéro.

### 🔍 Validation

```bash
dsoxlab check first-infra-clean-destroy
```

Cinq tests. Le garde-fou est jugé sur le **code de retour** et non sur le
message : un texte change avec les versions. Le plan de destruction est jugé sur
le **nombre d'adresses**, parce qu'un test qui vérifierait la seule existence du
fichier passerait sur un plan mutilé.
