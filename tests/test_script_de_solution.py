"""Méta-tests du dépôt : le script de solution est-il vraiment joué ?

`conftest.py` et `scripts/verify-solutions.py` savent désormais exécuter un
`solution.sh` après avoir posé les fichiers d'une solution. C'est ce qui rend
jouables les labs dont la correction n'est pas un fichier mais un GESTE :
« enregistre un plan avec `-out`, relis-le en JSON, applique ce plan-là ».

Un mécanisme de ce genre se vérifie dans les deux sens, sinon il finit par ne
plus rien faire sans que personne ne s'en aperçoive :

- un script qui réussit doit laisser sa trace, et disparaître du workdir ;
- un script qui échoue doit remonter bruyamment, avec sa sortie.

Le second point est le plus important. Une solution de référence qui casse en
silence rendrait tous les tests d'un lab rouges sans dire pourquoi.
"""

from pathlib import Path

import pytest

from conftest import SCRIPT_SOLUTION, _jouer_script_de_solution


def test_un_script_qui_reussit_laisse_sa_trace_et_disparait(tmp_path: Path) -> None:
    (tmp_path / SCRIPT_SOLUTION).write_text(
        "#!/usr/bin/env bash\nset -eu\nprintf 'fait\\n' > temoin.txt\n",
        encoding="utf-8",
    )

    _jouer_script_de_solution(tmp_path)

    assert (tmp_path / "temoin.txt").read_text(encoding="utf-8") == "fait\n", (
        "Le script n'a pas été exécuté dans le workdir."
    )
    assert not (tmp_path / SCRIPT_SOLUTION).exists(), (
        "Le script est resté dans le workdir. Il est le MOYEN d'atteindre "
        "l'état attendu, il n'en fait pas partie : un test qui le trouverait là "
        "mesurerait le mauvais objet."
    )


def test_un_script_qui_echoue_remonte_avec_sa_sortie(tmp_path: Path) -> None:
    (tmp_path / SCRIPT_SOLUTION).write_text(
        "#!/usr/bin/env bash\n"
        "set -eu\n"
        "printf 'avant la panne\\n'\n"
        "printf 'la raison exacte\\n' >&2\n"
        "exit 3\n",
        encoding="utf-8",
    )

    with pytest.raises(RuntimeError) as leve:
        _jouer_script_de_solution(tmp_path)

    message = str(leve.value)
    assert "code 3" in message, f"Le code retour n'est pas rapporté : {message}"
    assert "la raison exacte" in message, (
        f"La sortie d'erreur du script n'est pas remontée : {message}"
    )
    assert "avant la panne" in message, (
        f"La sortie standard du script n'est pas remontée : {message}"
    )
    assert not (tmp_path / SCRIPT_SOLUTION).exists(), (
        "Le script doit être retiré même quand il échoue, sinon un second "
        "passage le rejouerait sur un workdir déjà à moitié corrigé."
    )


def test_aucun_script_n_est_exige(tmp_path: Path) -> None:
    """La très grande majorité des labs n'en a pas besoin, et doit continuer."""
    _jouer_script_de_solution(tmp_path)
    assert list(tmp_path.iterdir()) == []


def test_les_deux_materialisations_jouent_le_meme_script() -> None:
    """`conftest.py` et `verify-solutions.py` ne doivent pas diverger.

    Deux chemins matérialisent une solution : celui de pytest et celui du
    script de vérification. S'ils cessent de faire la même chose, une solution
    passera d'un côté et pas de l'autre, et le diagnostic partira sur le lab
    plutôt que sur le harnais.
    """
    import importlib.util

    chemin = Path(__file__).resolve().parent.parent / "scripts" / "verify-solutions.py"
    spec = importlib.util.spec_from_file_location("verify_solutions", chemin)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert module.SCRIPT_SOLUTION == SCRIPT_SOLUTION, (
        f"Les deux chemins cherchent des noms différents : "
        f"{module.SCRIPT_SOLUTION!r} contre {SCRIPT_SOLUTION!r}."
    )
    assert hasattr(module, "jouer_script_de_solution"), (
        "scripts/verify-solutions.py ne sait pas jouer de script de solution."
    )
