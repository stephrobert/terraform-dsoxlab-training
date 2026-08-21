# Valeur sentinelle du secret. Le test verifie qu'elle n'apparait NULLE PART
# dans terraform.tfstate : c'est toute la promesse d'un argument write-only.
secret_api = "WO-SENTINELLE-NE-DOIT-PAS-FUITER"
