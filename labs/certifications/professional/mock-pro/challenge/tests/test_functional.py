"""Examen blanc du Professional : six tâches, une par objectif.

Ce n'est pas un lab d'apprentissage, c'est une répétition générale, à jouer une
fois les six capstones réussis et **d'une traite**. Le temps fait partie de
l'épreuve : l'examen réel dure quatre heures et mêle QCM et travaux pratiques,
documentation ouverte.

## Une section de tests par tâche, et pourquoi

Chaque tâche est validée indépendamment des autres. Une tâche ratée ne doit pas
faire échouer les suivantes : le score dit alors QUEL objectif retravailler, ce
qui est le seul service qu'un examen blanc rend vraiment.

## Ce que ce mock ne fait pas, et c'est délibéré

**Il n'emploie aucun émulateur cloud.** Les six capstones et la section `aws` le
font déjà, avec Floci. Ici, une dépendance externe coûterait une à deux minutes
par exécution et une panne possible : un examen blanc doit pouvoir se lancer
d'un trait.

Ce choix a un prix, mesuré le 2026-09-25 : **aucun provider local ne supporte
l'import**. `local` comme `null` répondent « Resource Import Not Implemented ».
La tâche 1 éprouve donc l'autre moitié du sous-objectif 1e, la réconciliation
de dérive ; l'import est couvert par `capstone1-resource-lifecycle` et
`aws-import-moved-drift`, qui ont un vrai provider. De même, l'objectif 5 est
éprouvé sur l'aliasing et la contrainte de version plutôt que sur
l'authentification.

## Pas de question dont la réponse se lise dans l'état, et pourquoi

`mock-004` croise ses deux moitiés : quatre de ses questions portent sur l'état
de son propre atelier, les tests le recalculent, et répondre sans construire
échoue. Ici ce croisement est impossible : les douze questions portent sur HCP
Terraform, que rien ne construit sans compte. Le garde-fou est ailleurs, et il
est plus large : cinq des six tâches sont des travaux pratiques notés sur
l'état, le QCM n'en est qu'une.

## Ce que les tests lisent

`terraform show -json` et `terraform output -json`, et pour la tâche 1 le
contenu du fichier importé : c'est le seul moyen de distinguer un import réussi
d'un fichier recréé, puisque les deux donnent un state qui a l'air juste.
"""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from conftest import exiger_workdir, output_json, show_json, terraform, workdir_lab

WORKDIR = workdir_lab(__file__)
LAB_ID = "certifications-professional-mock-pro"

T1, T2, T3, T4, T5, T6 = (
    "t1-derive",
    "t2-dynamique",
    "t3-etats",
    "t4-module",
    "t5-providers",
    "t6-hcp",
)

CONTENU_EXISTANT = "inventaire du parc, corrige a la main le 2026-09-24\n"
SERVICES = {"api": 8080, "web": 8443, "batch": 9000}
ENVIRONNEMENTS = {"dev": 1, "staging": 2, "prod": 4}

SCORE_MINIMAL_T6 = 75
SOUS_OBJECTIFS = {"6a", "6b", "6c", "6d"}


@pytest.fixture(scope="module")
def joue() -> Path:
    exiger_workdir(WORKDIR, LAB_ID)
    return WORKDIR


def _appliquer(repertoire: Path, ou: str) -> None:
    init = terraform("init", "-input=false", "-no-color", cwd=repertoire)
    assert init.returncode == 0, f"`init` a échoué dans `{ou}`.\n{init.stderr[-700:]}"
    applique = terraform(
        "apply", "-auto-approve", "-input=false", "-no-color", cwd=repertoire
    )
    assert applique.returncode == 0, (
        f"`apply` a échoué dans `{ou}`.\n{(applique.stderr or applique.stdout)[-1200:]}"
    )


def _ressources(etat: dict) -> list[dict]:
    return (etat.get("values") or {}).get("root_module", {}).get("resources", [])


def _toutes_ressources(etat: dict) -> list[dict]:
    """Les ressources de la racine ET des modules appelés."""
    racine = (etat.get("values") or {}).get("root_module", {})
    trouvees = list(racine.get("resources", []))
    for enfant in racine.get("child_modules", []) or []:
        trouvees += enfant.get("resources", [])
    return trouvees


# ===========================================================================
# Tâche 1, objectif 1 : réconcilier une dérive sans écraser.
# ===========================================================================
@pytest.fixture(scope="module")
def tache1(joue: Path) -> Path:
    repertoire = joue / T1
    _appliquer(repertoire, T1)
    return repertoire


def test_t1_le_fichier_existant_n_a_pas_ete_ecrase(tache1: Path) -> None:
    """Le seul test qui lit le fichier, et c'est le seul moyen de trancher.

    Adopter l'état réel et l'écraser donnent tous deux un state qui a l'air
    juste et un plan stable. Ce qui les distingue est le CONTENU : écraser
    aurait perdu la ligne que quelqu'un a corrigée à la main.
    """
    fichier = tache1 / "existant.txt"
    assert fichier.is_file(), "`existant.txt` a disparu : il a été détruit."

    contenu = fichier.read_text(encoding="utf-8")
    assert contenu == CONTENU_EXISTANT, (
        f"`existant.txt` contient {contenu!r}.\n\nLe fichier avait été corrigé "
        "à la main, et l'examen demande d'ADOPTER cet état, pas de l'écraser. "
        "Son contenu doit être inchangé."
    )


def test_t1_la_ressource_est_geree_et_le_plan_est_stable(tache1: Path) -> None:
    etat = show_json(tache1)
    gerees = [r for r in _ressources(etat) if r.get("mode") == "managed"]
    assert len(gerees) == 1, (
        f"{len(gerees)} ressource(s) gérée(s), une attendue : {[r['address'] for r in gerees]}"
    )

    plan = terraform("plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=tache1)
    assert plan.returncode == 0, (
        f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n\nLe "
        "fichier est géré, mais la configuration ne décrit pas son état réel : "
        "c'est une dérive non réconciliée.\n" + plan.stdout[-600:]
    )


# ===========================================================================
# Tâche 2, objectif 2 : réparer et rendre dynamique.
# ===========================================================================
@pytest.fixture(scope="module")
def tache2(joue: Path) -> Path:
    repertoire = joue / T2
    _appliquer(repertoire, T2)
    return repertoire


def test_t2_les_trois_fichiers_viennent_d_une_seule_ressource(tache2: Path) -> None:
    etat = show_json(tache2)
    fichiers = [r for r in _ressources(etat) if r["type"] == "local_file"]
    assert len(fichiers) == 3, f"{len(fichiers)} fichier(s), trois attendus."

    noms = {r.get("name") for r in fichiers}
    assert len(noms) == 1, (
        f"Les trois fichiers viennent de {len(noms)} ressources différentes : "
        f"{sorted(noms)}.\n\nL'examen demande UNE ressource portée par "
        "`for_each`, pas trois copies."
    )

    index = [r.get("index") for r in fichiers]
    assert all(isinstance(i, str) for i in index), (
        f"Les index valent {index} : ce sont des entiers, donc `count`. "
        "`for_each` produit des index nommés."
    )
    assert set(index) == set(SERVICES), (
        f"Index obtenus : {sorted(str(i) for i in index)}, attendu {sorted(SERVICES)}."
    )


def test_t2_chaque_fichier_porte_son_port(tache2: Path) -> None:
    etat = show_json(tache2)
    for ressource in (r for r in _ressources(etat) if r["type"] == "local_file"):
        nom = ressource["index"]
        contenu = ressource["values"]["content"]
        assert str(SERVICES[nom]) in contenu, (
            f"Le fichier `{nom}` contient {contenu!r} et ne cite pas son port "
            f"{SERVICES[nom]}."
        )


def test_t2_un_port_hors_plage_est_refuse_au_plan(tache2: Path, tmp_path: Path) -> None:
    """La validation doit refuser AVANT de créer quoi que ce soit.

    Éprouvée dans une copie jetable : un test qui vérifierait seulement la
    présence d'un bloc `validation` ne dirait pas s'il refuse réellement.
    """
    copie = tmp_path / "hors-plage"
    shutil.copytree(tache2, copie, symlinks=True)

    plan = terraform(
        "plan", "-input=false", "-no-color",
        "-var", 'services={"api":80}',
        cwd=copie,
    )
    assert plan.returncode != 0, (
        "Un port de 80 a été accepté au plan.\n\nLa variable doit porter une "
        "`validation` qui refuse tout port hors de 1024-65535 : sans elle, la "
        "faute ne se voit qu'à l'exécution."
    )


# ===========================================================================
# Tâche 3, objectif 3 : deux états qui communiquent.
# ===========================================================================
@pytest.fixture(scope="module")
def tache3(joue: Path) -> Path:
    racine = joue / T3
    _appliquer(racine / "socle", f"{T3}/socle")
    _appliquer(racine / "app", f"{T3}/app")
    return racine


def test_t3_l_application_lit_l_etat_du_socle(tache3: Path) -> None:
    etat = show_json(tache3 / "app")
    lues = [
        r for r in _ressources(etat)
        if r.get("mode") == "data" and r["type"] == "terraform_remote_state"
    ]
    assert lues, (
        "Aucune source de données `terraform_remote_state` dans l'état de "
        "`app`.\n\nLes deux racines doivent communiquer par l'état, pas par une "
        "valeur recopiée."
    )


def test_t3_la_valeur_traverse_les_deux_etats(tache3: Path) -> None:
    socle = output_json(tache3 / "socle")
    app = output_json(tache3 / "app")
    assert app["reseau_consomme"]["value"] == socle["identifiant_reseau"]["value"], (
        "`app` n'expose pas la valeur du socle."
    )


def test_t3_la_valeur_n_est_pas_recopiee_en_dur(tache3: Path, tmp_path: Path) -> None:
    """Le test qui distingue une lecture d'une copie.

    On rejoue le socle avec une autre zone dans une copie jetable : le
    `keepers` du `random_pet` fait changer l'identifiant. Si `app` suit, c'est
    qu'il lit ; s'il ne suit pas, la valeur avait été recopiée.
    """
    copie = tmp_path / "derive"
    shutil.copytree(tache3, copie, symlinks=True)

    rejoue = terraform(
        "apply", "-auto-approve", "-input=false", "-no-color",
        "-var", "zone=eu-west-1b",
        cwd=copie / "socle",
    )
    assert rejoue.returncode == 0, f"Rejeu du socle : {rejoue.stderr[-500:]}"

    apres = output_json(copie / "socle")["identifiant_reseau"]["value"]
    terraform("apply", "-auto-approve", "-input=false", "-no-color", cwd=copie / "app")

    assert output_json(copie / "app")["reseau_consomme"]["value"] == apres, (
        "Après avoir rejoué le socle avec une autre zone, `app` n'expose plus "
        "la même valeur que lui : la donnée a été RECOPIÉE au lieu d'être lue "
        "dans l'état distant."
    )


# ===========================================================================
# Tâche 4, objectif 4 : factoriser sans rien recréer.
# ===========================================================================
@pytest.fixture(scope="module")
def tache4(joue: Path) -> Path:
    repertoire = joue / T4
    _appliquer(repertoire, T4)
    return repertoire


def test_t4_les_trois_environnements_passent_par_un_module(tache4: Path) -> None:
    etat = show_json(tache4)
    racine = (etat.get("values") or {}).get("root_module", {})
    modules = racine.get("child_modules", []) or []

    assert len(modules) >= 3, (
        f"{len(modules)} appel(s) de module, trois attendus.\n\nLes trois "
        "environnements doivent passer par un module local, pas rester trois "
        "blocs recopiés."
    )
    assert not [r for r in racine.get("resources", []) if r["type"] == "local_file"], (
        "Des `local_file` subsistent à la racine : la factorisation est "
        "incomplète."
    )


def test_t4_rien_n_a_ete_recree_et_le_plan_est_stable(tache4: Path) -> None:
    """La moitié qui compte : une factorisation qui recrée tout est un échec.

    C'est ce que les blocs `moved` évitent, et c'est ce que l'examen vérifie.
    """
    plan = terraform("plan", "-detailed-exitcode", "-input=false", "-no-color", cwd=tache4)
    assert plan.returncode == 0, (
        f"`plan -detailed-exitcode` rend {plan.returncode}, attendu 0.\n\nSi le "
        "plan annonce des destructions et des créations, les blocs `moved` "
        "manquent : Terraform ne peut pas deviner où chaque ressource a "
        "déménagé.\n" + plan.stdout[-800:]
    )

    sorties = output_json(tache4)
    empreintes = sorties.get("empreintes", {}).get("value", {})
    assert set(empreintes) == set(ENVIRONNEMENTS), (
        f"`empreintes` porte {sorted(empreintes)}, attendu {sorted(ENVIRONNEMENTS)}."
    )


# ===========================================================================
# Tâche 5, objectif 5 : deux configurations d'un même provider.
# ===========================================================================
@pytest.fixture(scope="module")
def tache5(joue: Path) -> Path:
    repertoire = joue / T5
    _appliquer(repertoire, T5)
    return repertoire


def test_t5_le_repertoire_prive_est_ferme(tache5: Path) -> None:
    """Les droits se posent sur la RESSOURCE, jamais sur le provider `local`.

    Mesuré le 2026-09-25 : le schéma de configuration de `hashicorp/local` est
    vide. Un `directory_permission` placé dans le bloc `provider` fait échouer
    l'apply sur « An argument named "directory_permission" is not expected
    here ». C'est le piège de la tâche.
    """
    public = tache5 / "public"
    prive = tache5 / "prive"
    assert public.is_dir() and prive.is_dir(), (
        "Les deux répertoires n'ont pas été créés : l'apply n'est pas allé au "
        "bout, ou les chemins ont été changés."
    )

    droits_prive = oct(prive.stat().st_mode)[-3:]
    droits_public = oct(public.stat().st_mode)[-3:]
    assert droits_prive == "700", (
        f"`prive/` est en {droits_prive}, attendu 700.\n\nLe répertoire que "
        "Terraform crée au passage prend `directory_permission`, un argument de "
        "la ressource `local_file`."
    )
    assert droits_public != droits_prive, (
        f"`public/` et `prive/` sont tous deux en {droits_prive} : les droits "
        "ont été posés des deux côtés, alors que `public/` garde le défaut."
    )

    fichier = prive / "note.txt"
    assert fichier.is_file(), "`prive/note.txt` manque."
    droits_fichier = oct(fichier.stat().st_mode)[-3:]
    assert droits_fichier == "600", (
        f"`prive/note.txt` est en {droits_fichier}, attendu 600. Le fichier a "
        "son propre argument, `file_permission` ; fermer le répertoire ne "
        "ferme pas ce qu'il contient."
    )


def test_t5_les_deux_fichiers_ne_sont_pas_rendus_par_la_meme_configuration(
    tache5: Path,
) -> None:
    """Le rattachement se lit dans le state, et nulle part ailleurs.

    `terraform show -json` d'un state rend le même `provider_name` pour les
    deux ressources, alias compris : mesuré le 2026-09-25. Seul le state brut
    porte la clé complète, `provider["...local"].restreint`.
    """
    etat = tache5 / "terraform.tfstate"
    assert etat.is_file(), "Aucun state : l'apply n'a pas abouti."

    rattachements = {
        f"{r['type']}.{r['name']}": r["provider"]
        for r in json.loads(etat.read_text(encoding="utf-8"))["resources"]
    }
    manquantes = {"local_file.public", "local_file.prive"} - set(rattachements)
    assert not manquantes, f"Absentes du state : {sorted(manquantes)}."

    prive = rattachements["local_file.prive"]
    public = rattachements["local_file.public"]
    assert prive != public, (
        "Les deux fichiers sont rendus par la même configuration de provider "
        f"({public}).\n\n`local_file.prive` doit porter un argument "
        "`provider`, sans quoi il prend la configuration par défaut sans rien "
        "dire."
    )
    assert "]." in prive, (
        f"`local_file.prive` est rattaché à {prive}, qui ne nomme aucun alias. "
        "Une configuration aliasée s'écrit `provider[\"...\"].<alias>` dans le "
        "state."
    )
    assert "]." not in public, (
        f"`local_file.public` est rattaché à {public}, une configuration "
        "aliasée. C'est l'inverse : le public garde la configuration par "
        "défaut, le privé prend l'alias."
    )


def test_t5_la_contrainte_encadre_la_serie_et_a_pilote_l_installation(
    tache5: Path,
) -> None:
    """Deux moitiés, et la seconde n'est atteignable qu'après la première.

    Le fichier de verrouillage est écrit par `init` : il dit la contrainte qui
    a réellement servi et la version qu'elle a laissée passer. Lire
    `versions.tf` ne dirait que ce qui est écrit.

    Mesuré le 2026-09-25 : `~> 2.5` résout en 2.9.1. Un test qui exigerait une
    2.5.x recalerait donc la bonne réponse.
    """
    verrou = tache5 / ".terraform.lock.hcl"
    assert verrou.is_file(), "Aucun fichier de verrouillage : `init` n'a pas tourné."

    lu = {}
    for ligne in verrou.read_text(encoding="utf-8").splitlines():
        for cle in ("version", "constraints"):
            if ligne.strip().startswith(cle) and cle not in lu:
                lu[cle] = ligne.split("=", 1)[1].strip().strip('"')

    contrainte = lu.get("constraints", "")
    assert "~>" in contrainte, (
        f"La contrainte enregistrée est `{contrainte}`.\n\n`>= 2.5` laisserait "
        "passer la 3.0 le jour où elle sortira, et une version exacte "
        "interdirait les correctifs. L'opérateur pessimiste dit les deux à la "
        "fois."
    )

    version = tuple(int(n) for n in lu.get("version", "0").split("."))
    assert (2, 5, 0) <= version < (3, 0, 0), (
        f"Le provider installé est en {lu.get('version')}, hors de la série "
        "attendue. La contrainte écrite n'encadre pas ce qui a été résolu."
    )


# ===========================================================================
# Tâche 6, objectif 6 : le QCM.
# ===========================================================================
@pytest.fixture(scope="module")
def tache6(joue: Path) -> dict:
    repertoire = joue / T6
    _appliquer(repertoire, T6)
    return {c: v["value"] for c, v in output_json(repertoire).items()}


def test_t6_aucune_question_n_est_laissee_sans_reponse(tache6: dict) -> None:
    sans = tache6.get("sans_reponse", [])
    assert sans == [], (
        f"{len(sans)} question(s) sans réponse : {sans}\n\nÀ l'examen, une "
        "question laissée vide est une question perdue."
    )


def test_t6_le_score_atteint_le_seuil_avec_un_bareme_intact(tache6: dict) -> None:
    """Deux moitiés dans un seul test, et la première explique pourquoi.

    « Le barème porte douze empreintes sha256 » est vrai AVANT tout travail :
    le barème est fourni. Mesuré le 2026-09-25, ce contrôle isolé rendait
    6/100 sur l'état de départ, ce qui est le défaut que ce dépôt traque le
    plus souvent : un test vert sans rien faire n'est pas un test, c'est une
    hypothèse du setup.

    Réuni au score, il reprend son sens : il refuse un score obtenu en ayant
    remplacé les empreintes par celles de ses propres réponses.
    """
    empreintes = tache6.get("empreintes", {})
    assert len(empreintes) == 12, f"{len(empreintes)} empreintes, douze attendues."
    for question, valeur in empreintes.items():
        assert len(valeur) == 64 and all(c in "0123456789abcdef" for c in valeur), (
            f"L'empreinte de `{question}` n'est pas un sha256 : le barème a été "
            "modifié, et un score obtenu ainsi ne mesure plus rien."
        )

    score = tache6.get("score")
    assert score >= SCORE_MINIMAL_T6, (
        f"Le QCM rend {score}/100, {SCORE_MINIMAL_T6} attendus.\n\n"
        f"Détail : {tache6.get('score_par_sous_objectif')}\n"
        "Les questions fausses se lisent dans l'output `corrige`."
    )


def test_t6_les_quatre_sous_objectifs_sont_couverts(tache6: dict) -> None:
    par_objectif = tache6.get("score_par_sous_objectif", {})
    assert set(par_objectif) == SOUS_OBJECTIFS, (
        f"Sous-objectifs notés : {sorted(par_objectif)}, attendu "
        f"{sorted(SOUS_OBJECTIFS)}."
    )
    faibles = {o: s for o, s in par_objectif.items() if s < 50}
    assert not faibles, (
        f"Ces sous-objectifs sont sous 50 % : {faibles}.\n\nUn score global "
        "correct peut masquer un objectif non maîtrisé : c'est précisément ce "
        "qu'un examen blanc doit faire voir."
    )
