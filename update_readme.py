"""
Met à jour automatiquement, dans README.md, le bloc compris entre
<!-- PROJECTS:START --> et <!-- PROJECTS:END -->.

Pour chaque repo listé dans FEATURED_REPOS, le script va chercher en direct
sur l'API GitHub :
  - la description du repo (celle que tu écris dans "About" sur GitHub)
  - le langage principal + jusqu'à 4 langages détectés dans le code
  - le lien direct vers le repo

Aucune donnée n'est écrite en dur : si tu changes la description d'un repo
sur GitHub, ou si tu ajoutes du TypeScript à un projet qui n'était qu'en
JS, le README se met à jour tout seul au prochain run.

Pour ajouter/retirer un projet mis en avant : modifie juste la liste
FEATURED_REPOS ci-dessous (aucune autre logique à toucher).
"""

import os
import re
import sys
import requests

USERNAME = "yasserbadri"

FEATURED_REPOS = [
    "DocLink",
    "Deephire",
    "EasyPark",
    "CovoiturageApp",
    "EasyFreelance",
    "AI_Content_Platform",
]

README_PATH = "README.md"
START_MARK = "<!-- PROJECTS:START -->"
END_MARK = "<!-- PROJECTS:END -->"

TOKEN = os.environ.get("GITHUB_TOKEN")
HEADERS = {"Accept": "application/vnd.github+json"}
if TOKEN:
    HEADERS["Authorization"] = f"Bearer {TOKEN}"

API = "https://api.github.com"

# Couleurs GitHub officielles pour quelques langages courants (fallback: gris)
LANG_COLORS = {
    "Python": "3776AB", "JavaScript": "F7DF1E", "TypeScript": "3178C6",
    "Java": "ED8B00", "HTML": "E34F26", "CSS": "1572B6", "C#": "239120",
    "Dart": "0175C2", "Angular": "DD0031", "PHP": "777BB4",
    "Vue": "4FC08D", "C": "A8B9CC", "Shell": "89E051", "Dockerfile": "384D54",
}


def fetch_repo(repo: str) -> dict | None:
    r = requests.get(f"{API}/repos/{USERNAME}/{repo}", headers=HEADERS, timeout=15)
    if r.status_code != 200:
        print(f"[warn] {repo}: repo introuvable ou privé ({r.status_code}), ignoré.")
        return None
    return r.json()


def fetch_languages(repo: str) -> dict[str, int]:
    r = requests.get(f"{API}/repos/{USERNAME}/{repo}/languages", headers=HEADERS, timeout=15)
    if r.status_code != 200:
        return {}
    return r.json()


def lang_badge(name: str) -> str:
    color = LANG_COLORS.get(name, "6b7268")
    label = name.replace(" ", "%20").replace("-", "--")
    return f"![{name}](https://img.shields.io/badge/{label}-{color}?style=flat-square&logoColor=white)"


def build_card(repo: str) -> str | None:
    data = fetch_repo(repo)
    if data is None:
        return None

    description = data.get("description") or "No description provided."
    url = data.get("html_url", f"https://github.com/{USERNAME}/{repo}")

    languages = fetch_languages(repo)
    top_langs = sorted(languages.items(), key=lambda kv: -kv[1])[:4]
    badges = " ".join(lang_badge(name) for name, _ in top_langs) or "_No language detected_"

    return (
        f"<td width=\"50%\" valign=\"top\">\n\n"
        f"**[{repo}]({url})**\n"
        f"{description}\n\n"
        f"{badges}\n\n"
        f"</td>"
    )


def build_table(cards: list[str]) -> str:
    rows = []
    for i in range(0, len(cards), 2):
        pair = cards[i:i + 2]
        rows.append("<tr>\n" + "\n".join(pair) + "\n</tr>")
    return "<table>\n" + "\n".join(rows) + "\n</table>"


def main() -> None:
    cards = []
    for repo in FEATURED_REPOS:
        card = build_card(repo)
        if card:
            cards.append(card)

    if not cards:
        print("[error] Aucun projet récupéré, README non modifié.")
        sys.exit(1)

    new_block = f"{START_MARK}\n\n{build_table(cards)}\n\n{END_MARK}"

    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(re.escape(START_MARK) + r".*?" + re.escape(END_MARK), re.DOTALL)
    if not pattern.search(content):
        print(f"[error] Marqueurs {START_MARK} / {END_MARK} introuvables dans {README_PATH}.")
        sys.exit(1)

    updated = pattern.sub(new_block, content)

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)

    print(f"[ok] README mis à jour avec {len(cards)} projet(s).")


if __name__ == "__main__":
    main()
