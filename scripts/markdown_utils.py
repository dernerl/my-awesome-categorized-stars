"""Hilfsfunktionen für die Markdown-Reports."""

import unicodedata


def github_anchor(heading: str) -> str:
    """Erzeugt den Anker, den GitHub für eine Markdown-Überschrift vergibt.

    Nachbau von github-slugger: kleinschreiben, alles außer Buchstaben,
    Ziffern, Leerzeichen, '-' und '_' entfernen (Emojis, '&', ',', '(' …),
    dann jedes Leerzeichen einzeln durch '-' ersetzen. Umlaute bleiben,
    mehrfache Bindestriche werden NICHT zusammengefasst.
    Beispiel: '📂 DevOps, IT & Hosting' -> '-devops-it--hosting'
    """
    kept = []
    for char in heading.lower():
        category = unicodedata.category(char)
        if char in (' ', '-', '_') or category[0] in ('L', 'N') or (category[0] == 'M' and char != '️'):
            kept.append(char)
    return ''.join(kept).replace(' ', '-')
