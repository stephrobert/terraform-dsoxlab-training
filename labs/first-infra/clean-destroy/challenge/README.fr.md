# 🎯 Challenge : détruire proprement

## Point de départ

`challenge/work` contient quatre ressources. Trois forment une chaîne de
dépendances, la quatrième est un **témoin** indépendant. Le bloc `lifecycle` du
`local_file` est troué.

Aucun cloud, aucune VM, aucun appel réseau : tout est déterministe et rejouable.

## ✅ Objectif, dans cet ordre

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

## 🧭 Les quatre façons de détruire, et ce qui les distingue

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

## 🔍 Validation

```bash
dsoxlab check first-infra-clean-destroy
```

Cinq tests. Le garde-fou est jugé sur le **code de retour** et non sur le
message : un texte change avec les versions. Le plan de destruction est jugé sur
le **nombre d'adresses**, parce qu'un test qui vérifierait la seule existence du
fichier passerait sur un plan mutilé.
