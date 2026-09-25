#!/usr/bin/env python3
"""Génère la table des labs (id, titre, niveau, certif, runtime, guide) dans les README.

Source de vérité : l'ordre des sections de `meta.yml` plus chaque
`labs/**/lab.yaml` (et `lab.fr.yaml` pour le titre français). La table s'écrit
entre les marqueurs `<!-- LABS:START -->` et `<!-- LABS:END -->` de `README.md`
et `README.fr.md`.

Repris du catalogue Linux, avec trois différences que CE dépôt impose :

1. **Une cellule vide s'écrit `-`, jamais `—`.** La règle de style du dépôt
   interdit le tiret cadratin dans ce que l'apprenant lit, et la table du README
   en fait partie. Le générateur d'origine posait un cadratin.

2. **La colonne `Runtime` dit ce qu'il faut pour jouer.** Tous les labs sont en
   `runtime: shell`, ce qui rendrait la colonne muette : elle affiche donc le
   service que le lab démarre quand il en déclare un (`shell + floci`), et
   `shell + compte HCP` pour le seul lab qui exige un compte. Un apprenant lit
   cette colonne pour savoir ce qu'il doit avoir sous la main.

3. **Le titre français vient de `lab.fr.yaml`.** Les répertoires sont nommés en
   anglais et les sections aussi ; seule la colonne des titres bascule.

Usage :
    python3 scripts/gen_catalog.py            # régénère les README
    python3 scripts/gen_catalog.py --check    # échoue (exit 1) si un README est périmé
"""

from __future__ import annotations

import sys
from pathlib import Path

# Un seul chemin de lecture pour tout le catalogue : voir scripts/lecture_yaml.py.
sys.path.insert(0, str(Path(__file__).resolve().parent))
from lecture_yaml import YamlIllisible, lire_yaml  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
META = ROOT / "meta.yml"
START, END = "<!-- LABS:START -->", "<!-- LABS:END -->"

# Une cellule sans valeur. Pas de tiret cadratin : la règle de style du dépôt
# l'interdit dans ce que l'apprenant lit.
VIDE = "-"

HEAD = {
    "en": ("Lab (id)", "Title", "Level", "Certif", "Runtime", "Companion guide"),
    "fr": ("Lab (id)", "Titre", "Niveau", "Certif", "Runtime", "Guide compagnon"),
}

# Le seul lab qui exige un compte. Le dire dans la table évite qu'on le découvre
# en le lançant.
LAB_AVEC_COMPTE = "hcp-terraform-premier-run-distant"
MENTION_COMPTE = {"en": "shell + HCP account", "fr": "shell + compte HCP"}


def _runtime_label(lab: dict, lang: str) -> str:
    """Ce qu'il faut avoir sous la main pour jouer ce lab."""
    runtime = lab.get("runtime") or {}
    base = str(runtime.get("type", "shell"))

    if lab.get("id") == LAB_AVEC_COMPTE:
        return MENTION_COMPTE[lang]

    services = [s.get("name", "") for s in (runtime.get("services") or [])]
    if services:
        return f"{base} + " + ", ".join(sorted(n for n in services if n))
    return base


def _sections() -> list[tuple[str, str, list[dict]]]:
    """[(id de section, titre, [lab, ...]), ...] dans l'ordre de meta.yml."""
    try:
        meta = lire_yaml(META)
    except YamlIllisible as erreur:
        # Sans meta.yml il n'y a pas de catalogue du tout : on s'arrête en
        # DISANT quoi, pas sur une trace d'appels.
        sys.exit(f"catalogue ingénérable - {erreur}")

    trouvees: list[tuple[str, str, list[dict]]] = []
    for section in meta.get("sections", []):
        labs: list[dict] = []
        for rel in section.get("labs") or []:
            dossier = ROOT / "labs" / rel
            contrat = dossier / "lab.yaml"
            if not contrat.exists():
                continue
            try:
                lab = lire_yaml(contrat)
            except YamlIllisible as erreur:
                print(f"  lab écarté du catalogue - {rel}/{erreur}", file=sys.stderr)
                continue

            lab["_titre_fr"] = lab.get("title", "")
            contrat_fr = dossier / "lab.fr.yaml"
            if contrat_fr.exists():
                try:
                    fr = lire_yaml(contrat_fr)
                except YamlIllisible as erreur:
                    print(f"  {rel}/{erreur}", file=sys.stderr)
                    fr = {}
                lab["_titre_fr"] = fr.get("title", lab.get("title", ""))
            labs.append(lab)

        if labs:
            trouvees.append((section.get("id", ""), section.get("title", ""), labs))
    return trouvees


def _certif(lab: dict) -> str:
    """Les certifications visées, ex. « TF-ASSOCIATE »."""
    tags = lab.get("certification_tags") or []
    if not tags:
        return VIDE
    return " · ".join(str(t).upper() for t in tags)


def _guide(lab: dict) -> str:
    url = lab.get("doc_url", "")
    return f"[guide]({url})" if url else VIDE


def _echapper(texte: str) -> str:
    """Un titre peut porter un `|`, qui couperait la cellule en deux."""
    return str(texte).replace("|", "\\|")


def _table(lang: str) -> str:
    entetes = HEAD[lang]
    lignes: list[str] = []
    sections = _sections()

    for _id, titre, labs in sections:
        lignes.append(f"### {titre}")
        lignes.append("")
        lignes.append("| " + " | ".join(entetes) + " |")
        lignes.append("|" + "|".join(["---"] * len(entetes)) + "|")
        for lab in labs:
            titre_lab = lab["_titre_fr"] if lang == "fr" else lab.get("title", "")
            lignes.append(
                "| `{id}` | {titre} | {niveau} | {certif} | {rt} | {guide} |".format(
                    id=lab.get("id", ""),
                    titre=_echapper(titre_lab),
                    niveau=lab.get("level", VIDE),
                    certif=_certif(lab),
                    rt=_runtime_label(lab, lang),
                    guide=_guide(lab),
                )
            )
        lignes.append("")

    total = sum(len(labs) for _i, _t, labs in sections)
    legende = (
        f"_{total} labs, table generated by `scripts/gen_catalog.py`._"
        if lang == "en"
        else f"_{total} labs, table générée par `scripts/gen_catalog.py`._"
    )
    lignes.append(legende)
    return "\n".join(lignes)


def _rendu(chemin: Path, bloc: str) -> str:
    texte = chemin.read_text(encoding="utf-8")
    if START not in texte or END not in texte:
        raise SystemExit(f"marqueurs absents dans {chemin}")
    avant = texte.split(START)[0]
    apres = texte.split(END)[1]
    return f"{avant}{START}\n{bloc}\n{END}{apres}"


CIBLES = {"README.md": "en", "README.fr.md": "fr"}


def _verifier() -> int:
    perimes = []
    for nom, lang in CIBLES.items():
        chemin = ROOT / nom
        if chemin.read_text(encoding="utf-8") != _rendu(chemin, _table(lang)):
            perimes.append(nom)
    if perimes:
        print(
            "Catalogue périmé dans : "
            + ", ".join(perimes)
            + "\nLancez `python3 scripts/gen_catalog.py` puis recommitez.",
            file=sys.stderr,
        )
        return 1
    print("catalogue à jour")
    return 0


def _ecrire() -> None:
    for nom, lang in CIBLES.items():
        chemin = ROOT / nom
        chemin.write_text(_rendu(chemin, _table(lang)), encoding="utf-8")
    print("catalogue régénéré dans README.md et README.fr.md")


def main() -> None:
    if "--check" in sys.argv[1:]:
        raise SystemExit(_verifier())
    _ecrire()


if __name__ == "__main__":
    main()
