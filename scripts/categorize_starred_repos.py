#!/usr/bin/env python3
"""
GitHub Starred Repositories Categorizer
Verwendet OpenAI API um starred Repositories automatisch zu kategorisieren
"""

import os
import json
import requests
from datetime import datetime
from typing import List, Dict, Any
from github import Github
import openai

class StarredRepoCategorizer:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        self.github_username = os.getenv('GITHUB_USERNAME')
        
        # Debug: Print verfügbare Umgebungsvariablen
        print(f"GITHUB_TOKEN: {'✅' if self.github_token else '❌'}")
        print(f"OPENAI_API_KEY: {'✅' if self.openai_api_key else '❌'}")
        print(f"GITHUB_USERNAME: {self.github_username}")
        
        if not self.github_token:
            raise ValueError("Fehlende Umgebungsvariable: GITHUB_TOKEN")
        if not self.openai_api_key:
            raise ValueError("Fehlende Umgebungsvariable: OPENAI_API_KEY")
        if not self.github_username:
            raise ValueError("Fehlende Umgebungsvariable: GITHUB_USERNAME")
        
        self.github = Github(self.github_token)
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        
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
        """Kategorisiert Repositories mit OpenAI"""
        print("🤖 Starte KI-Kategorisierung...")
        
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

Antworte mit einem JSON-Objekt in folgendem Format:
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
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Du bist ein Experte für Software-Entwicklung und GitHub Repository-Organisation."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )
            
            ai_response = response.choices[0].message.content
            
            # Extrahiere JSON aus der Antwort
            json_start = ai_response.find('{')
            json_end = ai_response.rfind('}') + 1
            json_str = ai_response[json_start:json_end]
            
            categories = json.loads(json_str)
            
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
        except openai.OpenAIError as e:
            print(f"❌ OpenAI API Fehler: {e}")
            raise Exception(f"KI-Kategorisierung fehlgeschlagen: OpenAI API-Fehler - {e}")
        except Exception as e:
            print(f"❌ Unerwarteter Fehler bei KI-Kategorisierung: {e}")
            raise Exception(f"KI-Kategorisierung fehlgeschlagen: {e}")
    
    
    def generate_markdown_report(self, categorized_repos: Dict[str, List[Dict[str, Any]]]) -> str:
        """Generiert einen Markdown-Report"""
        report = f"""# 🌟 Meine kategorisierten GitHub Stars

*Letzte Aktualisierung: {datetime.now().strftime('%d.%m.%Y um %H:%M')}*

> 📚 **Setup & Dokumentation:** Siehe [Wiki](docs/Home.md) oder [Setup Guide](docs/SETUP.md)  
> 🤖 **Automatisch generiert** durch [GitHub Action](.github/workflows/categorize-starred-repos.yml)

"""
        
        total_repos = sum(len(repos) for repos in categorized_repos.values())
        report += f"📊 **Gesamt:** {total_repos} Repositories in {len(categorized_repos)} Kategorien\n\n"
        
        # Kategorien nach Anzahl sortieren
        sorted_categories = sorted(categorized_repos.items(), key=lambda x: len(x[1]), reverse=True)
        
        for category, repos in sorted_categories:
            report += f"## 📂 {category} ({len(repos)} Repos)\n\n"
            
            # Repositories nach Stars sortieren
            sorted_repos = sorted(repos, key=lambda x: x['stars'], reverse=True)
            
            for repo in sorted_repos:
                report += f"### [{repo['name']}]({repo['url']})\n"
                report += f"**{repo['description']}**\n\n"
                
                details = []
                if repo['language']:
                    details.append(f"🔹 **Sprache:** {repo['language']}")
                details.append(f"⭐ **Stars:** {repo['stars']:,}")
                details.append(f"🍴 **Forks:** {repo['forks']:,}")
                
                if repo['topics']:
                    details.append(f"🏷️ **Topics:** {', '.join(repo['topics'])}")
                
                if repo.get('categorization_reason'):
                    details.append(f"🤖 **KI-Begründung:** {repo['categorization_reason']}")
                
                report += "  \n".join(details) + "\n\n"
                report += "---\n\n"
        
        return report
    
    def save_results(self, categorized_repos: Dict[str, List[Dict[str, Any]]]):
        """Speichert Ergebnisse als JSON und Markdown"""
        # JSON für maschinelle Verarbeitung
        with open('starred_repos_categorized.json', 'w', encoding='utf-8') as f:
            json.dump(categorized_repos, f, indent=2, ensure_ascii=False, default=str)
        
        # Markdown für Menschen
        markdown_report = self.generate_markdown_report(categorized_repos)
        with open('README.md', 'w', encoding='utf-8') as f:
            f.write(markdown_report)
        
        print("✅ Ergebnisse gespeichert:")
        print("  - starred_repos_categorized.json (Rohdaten)")
        print("  - README.md (formatierter Report)")

def main():
    try:
        print("🚀 Starte Repository-Kategorisierung...")
        categorizer = StarredRepoCategorizer()
        
        # 1. Starred Repos laden
        print("\n📥 Lade starred Repositories...")
        starred_repos = categorizer.fetch_starred_repos()
        
        if not starred_repos:
            print("⚠️ Keine starred Repositories gefunden - Beende Ausführung")
            exit(0)  # Kein Fehler, einfach keine Repos
        
        # 2. KI-Kategorisierung
        print(f"\n🤖 Starte KI-Kategorisierung für {len(starred_repos)} Repositories...")
        categorized_repos = categorizer.categorize_with_ai(starred_repos)
        
        # 3. Ergebnisse speichern
        print("\n💾 Speichere Ergebnisse...")
        categorizer.save_results(categorized_repos)
        
        print("\n🎉 Kategorisierung erfolgreich abgeschlossen!")
        
    except ValueError as e:
        print(f"\n❌ Konfigurationsfehler: {e}")
        print("💡 Überprüfe die Umgebungsvariablen (GITHUB_TOKEN, OPENAI_API_KEY, GITHUB_USERNAME)")
        exit(1)
    except Exception as e:
        print(f"\n❌ Kritischer Fehler: {e}")
        print("💡 Die GitHub Action wird mit Fehlerstatus beendet")
        exit(1)

if __name__ == "__main__":
    main()