# A completer : cinq sorties.
#
#   env_effectif     la valeur qui a REELLEMENT gagne la precedence
#   region_effective idem
#   stack_name       le local calcule
#   sizing_total_mb  la memoire du sizing, multipliee par les replicas
#   manifest_path    le chemin du fichier ecrit
#
# `sizing_total_mb` est le seul qui prouve que le type complexe est consomme :
# un objet declare et jamais lu ne prouve rien.
