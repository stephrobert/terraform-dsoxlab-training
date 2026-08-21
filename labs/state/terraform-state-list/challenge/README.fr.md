# 🎯 Challenge : retrouver une adresse quand on ne connaît que l'identifiant

## ✅ Objectif

Dans `challenge/work`, tous les fichiers sont **complets et applicables**, sauf
un : **`reponses.auto.tfvars`**, qui porte cinq `???`.

Commencez par appliquer, sans quoi il n'y a rien à chercher :

```bash
terraform init
terraform apply
```

Trois outputs publient alors l'**identifiant** d'une instance tirée au sort, sans
jamais dire laquelle :

```bash
terraform output id_worker_recherche    # une instance de random_pet.worker  (count = 6)
terraform output id_service_recherche   # une instance de random_pet.service (for_each, 8 clés)
terraform output id_archive_recherche   # une archive du module stockage     (for_each, 5 clés)
```

À vous de remplir les cinq réponses :

1. **`adresse_worker`** : l'adresse de l'instance de `random_pet.worker` qui porte
   `id_worker_recherche`, indexée par **position**.
2. **`adresse_service`** : celle de l'instance de `random_pet.service`
   correspondante, indexée par **clé**.
3. **`adresse_archive`** : celle de l'archive correspondante, **qualifiée par le
   module**.
4. **`adresse_data_module`** : l'adresse complète de la data source déclarée dans
   `modules/stockage/`. Attention, elle ne commence pas par `data`.
5. **`nombre_managees`** : le nombre d'instances en `mode: managed` du state,
   modules **inclus**, data sources **exclues**.

Les adresses s'écrivent exactement comme `terraform state list` les affiche :
crochets, guillemets et préfixe de module compris. Sous `zsh`, quotez toute
adresse à crochets, sinon le shell la mange avant Terraform.

## 🔍 Validation

`dsoxlab check state-terraform-state-list` **reconstruit la vérité** depuis
`terraform show -json`, en descendant récursivement les `child_modules`, puis
résout lui-même chaque identifiant publié vers l'adresse qui le porte et compare
aux vôtres. Une réponse juste sur la ressource mais fausse sur l'index, sur la
clé ou sur le préfixe de module échoue.

Sont également prouvés, par exécution :

- une adresse **sans index** rend **toutes** les instances de la ressource, et
  une adresse de **module** est un filtre valide ;
- l'ordre de sortie suit la **profondeur de module**, pas l'alphabet ;
- les **quatre** diagnostics distincts d'une adresse qui ne correspond à rien,
  tous en code 1, alors qu'un `-id` sans correspondance rend **0** et une sortie
  vide ;
- la recette `state list | grep -v ^data | wc -l` rend bien **un de plus** que le
  vrai comptage : c'est la data source du module qu'elle compte à tort ;
- `plan -detailed-exitcode` rend 0 : lire le state ne change rien.

Bloqué ? `dsoxlab hint state-terraform-state-list`.
