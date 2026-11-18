#!/usr/bin/env python3
"""
GitHub Starred Repositories Categorizer
Verwendet Anthropic Claude API um starred Repositories automatisch zu kategorisieren
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any
from github import Github

from markdown_utils import github_anchor
import anthropic


class StarredRepoCategorizerClaude:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
        self.github_username = os.getenv('GITHUB_USERNAME')

        # Debug: Print verfügbare Umgebungsvariablen
        print(f"GITHUB_TOKEN: {'✅' if self.github_token else '❌'}")
        print(f"ANTHROPIC_API_KEY: {'✅' if self.anthropic_api_key else '❌'}")
        print(f"GITHUB_USERNAME: {self.github_username}")

        if not self.github_token:
            raise ValueError("Fehlende Umgebungsvariable: GITHUB_TOKEN")
        if not self.anthropic_api_key:
            raise ValueError("Fehlende Umgebungsvariable: ANTHROPIC_API_KEY")
        if not self.github_username:
            raise ValueError("Fehlende Umgebungsvariable: GITHUB_USERNAME")

        self.github = Github(self.github_token)
        self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)

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
        """Kategorisiert Repositories mit Claude"""
        print("🤖 Starte KI-Kategorisierung mit Claude...")

        # Bereite Repository-Daten für KI vor
        repo_summaries = []
        for repo in repos:
            summary = f"Repository: {repo['name']}\n"
            summary += f"Beschreibung: {repo['description']}\n"
            summary += f"Sprache: {repo['language'] or 'Unbekannt'}\n"
            summary += f"Topics: {', '.join(repo['topics']) if repo['topics'] else 'Keine'}\n"
            summary += f"Stars: {repo['stars']}\n"
            summary += "---\n"
            repo_summaries.append(summary)

        # KI-Prompt erstellen
        prompt = f"""
Analysiere die folgenden {len(repos)} GitHub Repositories und erstelle SELBSTSTÄNDIG sinnvolle Kategorien basierend auf den tatsächlichen Inhalten.

Repositories:
{''.join(repo_summaries)}

AUFGABE:
1. Analysiere alle Repositories nach Zweck, Funktion und Anwendungsbereich
2. Erkenne Muster und gemeinsame Themen
3. Erstelle passende Kategorien die die Repositories am besten beschreiben
4. Ignoriere Programmiersprachen - fokussiere auf ZWECK und FUNKTION

KATEGORISIERUNGS-PRINZIPIEN:
- Gruppiere nach praktischem Nutzen und Anwendungsbereich
- Erkenne Workflow-Zusammenhänge (z.B. "CI/CD & Deployment")
- Berücksichtige Zielgruppen (z.B. "System Admins", "Security Specialists")
- Erstelle 5-15 Kategorien (nicht zu viele, nicht zu wenige)
- Verwende präzise, aussagekräftige deutsche Namen
- Jedes Repository gehört in genau eine Kategorie

BEISPIELE für mögliche Kategorien (NUR als Inspiration, erstelle eigene):
- "Sicherheit & Authentifizierung"
- "Container & Orchestrierung"
- "Monitoring & Observability"
- "Infrastructure as Code"
- "Backup & Disaster Recovery"
- "Network & Connectivity"
- "Documentation & Knowledge Management"

Antworte NUR mit einem JSON-Objekt (ohne Markdown-Codeblöcke) in folgendem Format:
{{
  "Kategorie 1": [
    {{
      "name": "repo-name",
      "reason": "Warum dieses Repository in diese Kategorie gehört"
    }}
  ],
  "Kategorie 2": [...]
}}

Erstelle die Kategorien basierend auf den tatsächlichen Repositories, nicht basierend auf den Beispielen!
"""

        try:
            response = self.anthropic_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=8000,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                system="Du bist ein Experte für Software-Entwicklung und GitHub Repository-Organisation. Antworte immer mit validem JSON."
            )

            ai_response = response.content[0].text

            # Extrahiere JSON aus der Antwort (mehrere Strategien)
            categories = self._extract_json(ai_response)

            # Ordne vollständige Repository-Daten den Kategorien zu
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

        except json.JSONDecodeError as e:
            print(f"❌ Fehler beim Parsen der KI-Antwort: {e}")
            print(f"KI-Antwort war: {ai_response}")
            raise Exception(f"KI-Kategorisierung fehlgeschlagen: Ungültiges JSON-Format in der Antwort")
        except anthropic.APIError as e:
            print(f"❌ Anthropic API Fehler: {e}")
            raise Exception(f"KI-Kategorisierung fehlgeschlagen: Anthropic API-Fehler - {e}")
        except Exception as e:
            print(f"❌ Unerwarteter Fehler bei KI-Kategorisierung: {e}")
            raise Exception(f"KI-Kategorisierung fehlgeschlagen: {e}")

    def _extract_json(self, text: str) -> dict:
        """Extrahiert JSON aus der Antwort mit mehreren Strategien"""

        # Strategie 1: Direktes JSON-Parsing (Brace Counting)
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
                json_str = text[start:end]
                return json.loads(json_str)
        except json.JSONDecodeError:
            pass

        # Strategie 2: Code-Block-Extraktion
        try:
            import re
            code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)```', text)
            if code_block_match:
                return json.loads(code_block_match.group(1).strip())
        except (json.JSONDecodeError, AttributeError):
            pass

        # Strategie 3: Einfache Extraktion
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

🤖 *Generiert mit [Claude](https://www.anthropic.com/claude) von Anthropic*

---

## 📑 Inhaltsverzeichnis

"""

        # Kategorien nach Anzahl sortieren
        sorted_categories = sorted(categorized_repos.items(), key=lambda x: len(x[1]), reverse=True)

        # Inhaltsverzeichnis
        for category, repos in sorted_categories:
            anchor = github_anchor(f"📂 {category}")
            report += f"- [{category}](#{anchor}) ({len(repos)})\n"

        report += "\n---\n\n"

        # Kategorien mit Repos
        for category, repos in sorted_categories:
            report += f"## 📂 {category}\n\n"

            # Repositories nach Stars sortieren
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

        # Statistiken
        report += "---\n\n## 📊 Statistiken\n\n"
        report += "| Kategorie | Anzahl |\n"
        report += "|-----------|--------|\n"
        for category, repos in sorted_categories:
            report += f"| {category} | {len(repos)} |\n"
        report += f"| **Gesamt** | **{total_repos}** |\n"

        return report

    def save_results(self, categorized_repos: Dict[str, List[Dict[str, Any]]]):
        """Speichert Ergebnisse als JSON und Markdown"""

        # JSON mit Metadaten für maschinelle Verarbeitung
        output_data = {
            "last_updated": datetime.now().isoformat(),
            "total_repositories": sum(len(repos) for repos in categorized_repos.values()),
            "categories": categorized_repos,
            "generated_by": "Claude (Anthropic)"
        }

        with open('starred_repos_categorized_claude.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False, default=str)

        # Markdown für Menschen
        markdown_report = self.generate_markdown_report(categorized_repos)
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(markdown_report)

        print("✅ Ergebnisse gespeichert:")
        print("  - starred_repos_categorized_claude.json (Rohdaten)")
        print("  - README.md (formatierter Report)")


def main():
    try:
        print("🚀 Starte Repository-Kategorisierung mit Claude...")
        categorizer = StarredRepoCategorizerClaude()

        # 1. Starred Repos laden
        print("\n📥 Lade starred Repositories...")
        starred_repos = categorizer.fetch_starred_repos()

        if not starred_repos:
            print("⚠️ Keine starred Repositories gefunden - Beende Ausführung")
            exit(0)

        # 2. KI-Kategorisierung
        print(f"\n🤖 Starte Claude-Kategorisierung für {len(starred_repos)} Repositories...")
        categorized_repos = categorizer.categorize_with_ai(starred_repos)

        # 3. Ergebnisse speichern
        print("\n💾 Speichere Ergebnisse...")
        categorizer.save_results(categorized_repos)

        print("\n🎉 Kategorisierung erfolgreich abgeschlossen!")

    except ValueError as e:
        print(f"\n❌ Konfigurationsfehler: {e}")
        print("💡 Überprüfe die Umgebungsvariablen (GITHUB_TOKEN, ANTHROPIC_API_KEY, GITHUB_USERNAME)")
        exit(1)
    except Exception as e:
        print(f"\n❌ Kritischer Fehler: {e}")
        print("💡 Die GitHub Action wird mit Fehlerstatus beendet")
        exit(1)


if __name__ == "__main__":
    main()
