"""Tests fonctionnels — SQUELETTE.

Placeholder délibérément SKIPPÉ : un stub ne doit jamais passer au
vert sans rien prouver. À remplacer par des tests qui vérifient
l'état réel produit par le challenge (`terraform show -json`,
idempotence via `plan -detailed-exitcode`, destroy propre).
Helpers disponibles dans le conftest racine : terraform(),
show_json(), output_json().
"""
import pytest

pytestmark = pytest.mark.skip(
    reason="Lab squelette : tests à écrire (voir scenario.md)"
)


def test_placeholder() -> None:
    raise AssertionError("tests non implémentés")
