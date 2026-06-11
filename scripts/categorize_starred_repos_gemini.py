#!/usr/bin/env python3
"""
GitHub Starred Repositories Categorizer
Verwendet Google Gemini API um starred Repositories automatisch zu kategorisieren
"""

import os
import json
import re
import time
from datetime import datetime
from typing import List, Dict, Any
from github import Github
from google import genai
from google.genai import types as genai_types


class StarredRepoCategorizerGemini:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.gemini_api_key = os.getenv('GEMINI_API_KEY')
        self.github_username = os.getenv('GITHUB_USERNAME')

        print(f"GITHUB_TOKEN: {'✅' if self.github_token else '❌'}")
        print(f"GEMINI_API_KEY: {'✅' if self.gemini_api_key else '❌'}")
        print(f"GITHUB_USERNAME: {self.github_username}")

        if not self.github_token:
            raise ValueError("Fehlende Umgebungsvariable: GITHUB_TOKEN")
        if not self.gemini_api_key:
            raise ValueError("Fehlende Umgebungsvariable: GEMINI_API_KEY")
        if not self.github_username:
            raise ValueError("Fehlende Umgebungsvariable: GITHUB_USERNAME")

        self.github = Github(self.github_token)
        self.gemini = genai.Client(api_key=self.gemini_api_key)
        self.model_name = "gemini-3.5-flash"

    def fetch_starred_repos(self) -> List[Dict[str, Any]]:
        """Holt alle starred Repositories des Users"""
        print(f"Lade starred Repositories für {self.github_username}...")

        user = self.github.get_user(self.github_username)
        starred_repos = []

        for repo in user.get_starred():
            repo_data = {
                'name': repo.name,
                'full_name': repo.full_name,
                'description': repo.description or "Keine Beschreibung verfügbar",
                'language': repo.language,
                'topics': repo.get_topics(),
                'url': repo.html_url,
                'stars': repo.stargazers_count,
                'forks': repo.forks_count,
                'created_at': repo.created_at.isoformat(),
                'updated_at': repo.updated_at.isoformat()
            }
            starred_repos.append(repo_data)

        print(f"✅ {len(starred_repos)} starred Repositories gefunden")
        return starred_repos

    def categorize_with_ai(self, repos: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Kategorisiert Repositories mit Gemini"""
        print(f"🤖 Starte KI-Kategorisierung mit {self.model_name}...")

        repo_summaries = []
        for repo in repos:
            summary = f"Repository: {repo['name']}\n"
            summary += f"Beschreibung: {repo['description']}\n"
            summary += f"Sprache: {repo['language'] or 'Unbekannt'}\n"
            summary += f"Topics: {', '.join(repo['topics']) if repo['topics'] else 'Keine'}\n"
            summary += f"Stars: {repo['stars']}\n"
            summary += "---\n"
            repo_summaries.append(summary)

        prompt = f"""Analysiere die folgenden {len(repos)} GitHub Repositories und erstelle SELBSTSTÄNDIG sinnvolle Kategorien basierend auf den tatsächlichen Inhalten.

Repositories:
{''.join(repo_summaries)}

AUFGABE:
1. Analysiere alle Repositories nach Zweck, Funktion und Anwendungsbereich
2. Erkenne Muster und gemeinsame Themen
3. Erstelle passende Kategorien die die Repositories am besten beschreiben
4. Ignoriere Programmiersprachen - fokussiere auf ZWECK und FUNKTION

KATEGORISIERUNGS-PRINZIPIEN:
- Gruppiere nach praktischem Nutzen und Anwendungsbereich
- Erstelle 12-18 Kategorien — nicht weniger, nicht mehr
- Keine Kategorie darf mehr als 25 Repositories enthalten — wenn eine natürliche Gruppe größer ist, teile sie auf (z.B. "n8n & Workflow-Automatisierung" + "PowerShell & Windows-Administration")
- Verwende präzise, aussagekräftige deutsche Namen
- Jedes Repository gehört in genau eine Kategorie
- Bevorzuge spezifische Kategorienamen gegenüber generischen (z.B. "Intune & Endpoint Management" statt "Systemadministration")
- Jeder Kategoriename darf nur einmal vorkommen — keine Suffixe wie "(Erweiterung)" oder "(Teil 2)"
- Vermeide generische Catch-all-Kategorien wie "Diverses", "Allgemeines" oder "Sonstige Ressourcen"
- Benenne Kategorien nach ihrer FUNKTION, nicht nach der Technologie dahinter — statt "KI-gestützte Code-Generierung" lieber "Code-Generierung & Coding-Assistenten"; "KI-gestützt" darf maximal in 2 Kategorienamen vorkommen

Antworte NUR mit einem JSON-Objekt (ohne Markdown-Codeblöcke) in folgendem Format:
{{
  "Kategorie 1": [
    {{
      "name": "repo-name",
      "reason": "Warum dieses Repository in diese Kategorie gehört"
    }}
  ],
  "Kategorie 2": [...]
}}"""

        max_retries = 5
        last_error = None
        for attempt in range(max_retries):
            try:
                response = self.gemini.models.generate_content(
                    model=self.model_name,
                    contents=prompt,
                    config=genai_types.GenerateContentConfig(
                        temperature=0.3,
                        max_output_tokens=32768,
                        thinking_config=genai_types.ThinkingConfig(thinking_budget=0),
                    )
                )

                # Explicitly collect text from all non-thinking parts
                ai_response = ""
                if response.candidates:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'text') and part.text and not getattr(part, 'thought', False):
                            ai_response += part.text

                if not ai_response.strip():
                    # Fallback: try response.text directly
                    ai_response = response.text or ""

                print(f"📝 Antwort-Vorschau: {ai_response[:200]!r}")

                if not ai_response or not ai_response.strip():
                    raise Exception("Leere Antwort vom Modell erhalten")

                categories = self._extract_json(ai_response)

                categorized_repos = {}
                repo_lookup = {repo['name']: repo for repo in repos}

                for category, repo_list in categories.items():
                    categorized_repos[category] = []
                    for item in repo_list:
                        repo_name = item['name']
                        if repo_name in repo_lookup:
                            repo_data = repo_lookup[repo_name].copy()
                            repo_data['categorization_reason'] = item.get('reason', '')
                            categorized_repos[category].append(repo_data)

                print(f"✅ Repositories in {len(categorized_repos)} Kategorien eingeteilt")
                return categorized_repos

            except Exception as e:
                last_error = e
                if attempt < max_retries - 1:
                    wait = 30 * (2 ** attempt)
                    print(f"⚠️ Fehler (Versuch {attempt + 1}/{max_retries}), warte {wait}s: {str(e)[:120]}")
                    time.sleep(wait)
                else:
                    print(f"❌ Alle {max_retries} Versuche fehlgeschlagen: {e}")
                    raise Exception(f"KI-Kategorisierung fehlgeschlagen: {e}")
        raise Exception(f"KI-Kategorisierung nach {max_retries} Versuchen fehlgeschlagen: {last_error}")

    def _extract_json(self, text: str) -> dict:
        """Extrahiert JSON aus der Antwort mit mehreren Strategien"""
        try:
            code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
            if code_block_match:
                return json.loads(code_block_match.group(1).strip())
        except (json.JSONDecodeError, AttributeError):
            pass

        try:
            start = text.find('{')
            if start != -1:
                brace_count = 0
                end = start
                for i, char in enumerate(text[start:], start):
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
                        if brace_count == 0:
                            end = i + 1
                            break
                return json.loads(text[start:end])
        except json.JSONDecodeError:
            pass

        try:
            json_start = text.find('{')
            json_end = text.rfind('}') + 1
            if json_start != -1 and json_end > json_start:
                return json.loads(text[json_start:json_end])
        except json.JSONDecodeError:
            pass

        raise json.JSONDecodeError("Konnte kein JSON extrahieren", text, 0)

    def generate_markdown_report(self, categorized_repos: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generiert einen Markdown-Report"""
        total_repos = sum(len(repos) for repos in categorized_repos.values())

        report = f"""# 🌟 Meine kategorisierten GitHub Stars

📊 **{total_repos} Repositories** in **{len(categorized_repos)} Kategorien**

🕐 *Letzte Aktualisierung: {datetime.now().strftime('%d.%m.%Y um %H:%M Uhr')}*

🤖 *Generiert mit [Gemini 3.5 Flash](https://deepmind.google/technologies/gemini/) von Google*

---

## 📑 Inhaltsverzeichnis

"""
        sorted_categories = sorted(categorized_repos.items(), key=lambda x: len(x[1]), reverse=True)

        for category, repos in sorted_categories:
            anchor = category.lower().replace(' ', '-').replace('&', '').replace('/', '-')
            report += f"- [{category}](#{anchor}) ({len(repos)})\n"

        report += "\n---\n\n"

        for category, repos in sorted_categories:
            report += f"## 📂 {category}\n\n"

            sorted_repos = sorted(repos, key=lambda x: x['stars'], reverse=True)

            for repo in sorted_repos:
                report += f"### [{repo['name']}]({repo['url']})\n"
                report += f"{repo['description']}\n\n"

                details = []
                details.append(f"**Details:** ⭐ {repo['stars']:,}")
                if repo['language']:
                    details.append(f"`{repo['language']}`")
                if repo['topics']:
                    details.append(f"`{'`, `'.join(repo['topics'][:5])}`")

                report += " ".join(details) + "\n\n"

                if repo.get('categorization_reason'):
                    report += f"> 🤖 *{repo['categorization_reason']}*\n\n"

        report += "---\n\n## 📊 Statistiken\n\n"
        report += "| Kategorie | Anzahl |\n"
        report += "|-----------|--------|\n"
        for category, repos in sorted_categories:
            report += f"| {category} | {len(repos)} |\n"
        report += f"| **Gesamt** | **{total_repos}** |\n"

        return report

    def save_results(self, categorized_repos: Dict[str, List[Dict[str, Any]]]):
        """Speichert Ergebnisse als JSON und Markdown"""
        output_data = {
            "last_updated": datetime.now().isoformat(),
            "total_repositories": sum(len(repos) for repos in categorized_repos.values()),
            "categories": categorized_repos,
            "generated_by": "Gemini 3.5 Flash (Google)"
        }

        with open('starred_repos_categorized_gemini.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

        markdown_report = self.generate_markdown_report(categorized_repos)
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(markdown_report)

        print("✅ Ergebnisse gespeichert:")
        print("  - starred_repos_categorized_gemini.json (Rohdaten)")
        print("  - README.md (formatierter Report)")


def main():
    try:
        print("🚀 Starte Repository-Kategorisierung mit Gemini 3.5 Flash...")
        categorizer = StarredRepoCategorizerGemini()

        print("\n📥 Lade starred Repositories...")
        starred_repos = categorizer.fetch_starred_repos()

        if not starred_repos:
            print("⚠️ Keine starred Repositories gefunden - Beende Ausführung")
            exit(0)

        print(f"\n🤖 Starte Gemini-Kategorisierung für {len(starred_repos)} Repositories...")
        categorized_repos = categorizer.categorize_with_ai(starred_repos)

        print("\n💾 Speichere Ergebnisse...")
        categorizer.save_results(categorized_repos)

        print("\n🎉 Kategorisierung erfolgreich abgeschlossen!")

    except ValueError as e:
        print(f"\n❌ Konfigurationsfehler: {e}")
        print("💡 Überprüfe die Umgebungsvariablen (GITHUB_TOKEN, GEMINI_API_KEY, GITHUB_USERNAME)")
        exit(1)
    except Exception as e:
        print(f"\n❌ Kritischer Fehler: {e}")
        exit(1)


if __name__ == "__main__":
    main()
