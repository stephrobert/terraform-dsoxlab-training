# Ce qui bloque un run, et ce qui permet de passer outre

L'objectif 6 du Professional est le seul évalué **en QCM** : HashiCorp ne
demande aucune manipulation de HCP Terraform. Ce lab ne lance donc aucune
exécution distante et ne requiert **aucun compte**. Il fait raisonner, et
évaluer de vrais plans.

Le piège qu'il traite fait tomber les candidats : croire qu'un `hard-mandatory`
est indépassable.

## Ce n'est pas le niveau qui décide de l'override

C'est le **réglage du policy set**, croisé avec la **permission** de
l'utilisateur. La documentation est nette :

> Override capability is controlled by the **policy set setting**, not
> individual enforcement levels.

Le niveau ne décide que d'une chose : un `advisory` ne bloque jamais. Pour tout
le reste, deux conditions doivent être réunies :

| Le policy set autorise l'override | L'utilisateur a *Manage Policy Overrides* | Verdict |
| --- | --- | --- |
| oui | oui | bloqué, **surchargeable** |
| oui | non | **bloqué** |
| non | oui | **bloqué** |
| non | non | **bloqué** |

Un `hard-mandatory` dans un policy set ouvert, avec un utilisateur qui a le
droit, est donc surchargeable. Un `soft-mandatory` sans le droit ne l'est pas.

## Trois frameworks, trois vocabulaires

C'est l'autre source de confusion, et elle se lit plutôt qu'elle ne se devine :

| Framework | Niveaux |
| --- | --- |
| **Sentinel** | `advisory`, `soft-mandatory`, `hard-mandatory` |
| **OPA** | `advisory`, `mandatory` |
| **Terraform policy** | `advisory`, `mandatory overridable`, `mandatory` |

Trois niveaux d'un côté, deux de l'autre, et un intitulé qui nomme l'override
sans pour autant le garantir : c'est toujours le policy set qui tranche.

## Policy checks ou policy evaluations : l'ordre décide de ce qu'on voit

| | Quand | Framework | Voit le coût |
| --- | --- | --- | --- |
| **policy checks** | après l'estimation de coût | Sentinel seul, ≤ **0.40.x** | **oui** |
| **policy evaluations** | juste avant l'estimation | tous | non |

Ce n'est pas un détail d'implémentation : si votre règle porte sur le **coût**,
elle doit vivre dans un policy check, le mode historique. Une evaluation ne
verra jamais l'estimation, puisqu'elle passe avant.

## Ce que l'édition Free autorise

> HCP Terraform **Free** edition includes one policy set of up to five policies.

Un policy set, cinq policies, et pas de connexion à un dépôt : brancher un VCS
ou créer des versions par l'API est réservé aux éditions supérieures.

## Une règle dit où, pas seulement non

La seconde moitié du lab évalue deux **vraies** sorties de
`terraform show -json`, capturées avec le provider `local` : l'une crée un
fichier en `0640`, l'autre en `0777`.

La règle doit rendre les **adresses fautives**, pas un booléen :

```hcl
violations = {
  for nom, plan in local.plans : nom => [
    for c in plan.resource_changes : c.address
    if can(c.change.after.file_permission)
    && tonumber(substr(c.change.after.file_permission, 3, 1)) > 0
  ]
}
```

Une policy qui dit « non » sans dire « où » oblige celui qui la subit à
chercher. Et le `can()` n'est pas décoratif : toutes les ressources n'ont pas cet
attribut, et une expression qui suppose le contraire tombe au premier plan qui
porte autre chose qu'un fichier.

## Le jeton, et pourquoi vous n'en avez pas besoin

Ce lab ne demande **aucun compte HCP Terraform**, et rien ne part en exécution
distante. Si vous croisez

```
Error: Required token could not be found
```

c'est que votre configuration a été acceptée : Terraform en est à demander
l'authentification, et le lab s'arrête là volontairement.

Pour aller au-delà, un jeton se crée et se pose en trois minutes, et le guide
[`docs/hcp-token.fr.md`](../../../docs/hcp-token.fr.md) dit où le mettre et
lequel des emplacements l'emporte quand plusieurs sont remplis :

```bash
python3 scripts/diagnostic-jeton-hcp.py --verifier
```

## À vous de jouer

```bash
dsoxlab run hcp-terraform-policy-as-code
dsoxlab check hcp-terraform-policy-as-code
dsoxlab hint hcp-terraform-policy-as-code
```

Il se joue **hors ligne**, sans aucun provider : ce lab ne crée rien, il
raisonne et il lit.

Treize tests. Les sept cas sont assérés **un par un**, pour que le message dise
lequel est faux, et ils sont bâtis pour qu'aucune réponse constante ne passe. La
règle de conformité est éprouvée dans les **deux sens** : une règle qui refuse
tout échoue sur le plan conforme.

Sous-objectif d'examen visé : **6d**.

Référence : [gérer les policy sets dans HCP Terraform](https://developer.hashicorp.com/terraform/cloud-docs/policy-enforcement/manage-policy-sets)
