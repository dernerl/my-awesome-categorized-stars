#!/usr/bin/env python3
"""
GitHub Starred Repository Categorizer mit Atlassian Rovo Dev CLI
================================================================

Dieses Script:
1. Lädt alle starred GitHub Repositories eines Benutzers
2. Verwendet die Atlassian Rovo Dev CLI für die KI-basierte Kategorisierung
3. Speichert die kategorisierten Ergebnisse in einer JSON-Datei

Abhängigkeiten:
- PyGithub für GitHub API
- @atlassian/rovo-dev-cli (via npm)

Umgebungsvariablen:
- GITHUB_TOKEN: GitHub Personal Access Token
- GITHUB_USERNAME: GitHub Benutzername
- ATLASSIAN_EMAIL: Atlassian Account E-Mail
- ATLASSIAN_API_TOKEN: Atlassian API Token
"""

import os
import json
import subprocess
import tempfile
from typing import List, Dict, Any
from github import Github
from dotenv import load_dotenv

# Lade Umgebungsvariablen
load_dotenv()

class StarredRepoCategorizerRovo:
    def __init__(self):
        self.github_token = os.getenv('GITHUB_TOKEN')
        self.github_username = os.getenv('GITHUB_USERNAME')
        self.atlassian_email = os.getenv('ATLASSIAN_EMAIL')
        self.atlassian_token = os.getenv('ATLASSIAN_API_TOKEN')
        
        # Validiere Umgebungsvariablen
        if not all([self.github_token, self.github_username, self.atlassian_email, self.atlassian_token]):
            missing = []
            if not self.github_token: missing.append('GITHUB_TOKEN')
            if not self.github_username: missing.append('GITHUB_USERNAME')
            if not self.atlassian_email: missing.append('ATLASSIAN_EMAIL')
            if not self.atlassian_token: missing.append('ATLASSIAN_API_TOKEN')
            raise ValueError(f"Fehlende Umgebungsvariablen: {', '.join(missing)}")
        
        self.github = Github(self.github_token)
        print(f"✅ Initialisiert für Benutzer: {self.github_username}")
    
    def fetch_starred_repos(self) -> List[Dict[str, Any]]:
        """Lädt alle starred Repositories des Benutzers"""
        try:
            user = self.github.get_user(self.github_username)
            starred_repos = []
            
            print(f"📡 Lade starred Repositories für {self.github_username}...")
            
            for repo in user.get_starred():
                repo_data = {
                    'name': repo.name,
                    'full_name': repo.full_name,
                    'description': repo.description or 'Keine Beschreibung verfügbar',
                    'language': repo.language,
                    'topics': repo.get_topics(),
                    'stars': repo.stargazers_count,
                    'url': repo.html_url,
                    'created_at': repo.created_at.isoformat(),
                    'updated_at': repo.updated_at.isoformat()
                }
                starred_repos.append(repo_data)
            
            print(f"✅ {len(starred_repos)} Repositories geladen")
            return starred_repos
            
        except Exception as e:
            print(f"❌ Fehler beim Laden der Repositories: {e}")
            raise
    
    def prepare_prompt_for_rovo(self, repos: List[Dict[str, Any]]) -> str:
        """Erstellt einen Prompt für die Rovo CLI Kategorisierung"""
        repo_list = []
        for repo in repos:
            topics_str = ', '.join(repo['topics']) if repo['topics'] else 'keine'
            repo_info = f"- {repo['name']}: {repo['description']} (Sprache: {repo['language']}, Topics: {topics_str})"
            repo_list.append(repo_info)
        
        prompt = f"""Kategorisiere die folgenden {len(repos)} GitHub Repositories in sinnvolle Kategorien.

Repositories:
{chr(10).join(repo_list)}

Bitte gruppiere sie nach ihrem Hauptzweck/ihrer Hauptfunktion (z.B. "Web Development", "Machine Learning", "DevOps Tools", "Mobile Development", etc.).

Antworte nur mit einem gültigen JSON-Format:
{{
    "Kategorie 1": ["repo1", "repo2"],
    "Kategorie 2": ["repo3", "repo4"]
}}

Verwende die Repository-Namen (nicht die full_names) in den Arrays."""
        
        return prompt
    
    def categorize_with_rovo(self, repos: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Kategorisiert Repositories mit der Rovo Dev CLI"""
        if not repos:
            return {}
        
        try:
            # Erstelle Prompt
            prompt = self.prepare_prompt_for_rovo(repos)
            
            # Verwende temporäre Datei für den Prompt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(prompt)
                temp_file_path = temp_file.name
            
            try:
                print("🤖 Rufe Rovo Dev CLI für Kategorisierung auf...")
                
                # Rovo CLI Aufruf
                cmd = [
                    'rovo-dev',
                    'generate',
                    '--input-file', temp_file_path,
                    '--output-format', 'json'
                ]
                
                # Setze Atlassian Credentials als Umgebungsvariablen für CLI
                env = os.environ.copy()
                env['ATLASSIAN_EMAIL'] = self.atlassian_email
                env['ATLASSIAN_API_TOKEN'] = self.atlassian_token
                
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    env=env,
                    timeout=300  # 5 Minuten Timeout
                )
                
                if result.returncode != 0:
                    raise Exception(f"Rovo CLI Fehler: {result.stderr}")
                
                # Parse die JSON-Antwort
                ai_response = result.stdout.strip()
                print(f"🤖 Rovo Antwort erhalten ({len(ai_response)} Zeichen)")
                
                # Extrahiere JSON aus der Antwort (falls von Text umgeben)
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                
                if json_start == -1 or json_end == 0:
                    raise Exception("Keine gültige JSON-Struktur in der Rovo-Antwort gefunden")
                
                json_content = ai_response[json_start:json_end]
                categories = json.loads(json_content)
                
                # Konvertiere zu unserem Format
                result_categories = {}
                repo_lookup = {repo['name']: repo for repo in repos}
                
                for category, repo_names in categories.items():
                    result_categories[category] = []
                    for repo_name in repo_names:
                        if repo_name in repo_lookup:
                            result_categories[category].append(repo_lookup[repo_name])
                        else:
                            print(f"⚠️ Repository '{repo_name}' nicht in der ursprünglichen Liste gefunden")
                
                print(f"✅ Repositories in {len(result_categories)} Kategorien gruppiert")
                return result_categories
                
            finally:
                # Lösche temporäre Datei
                os.unlink(temp_file_path)
                
        except subprocess.TimeoutExpired:
            print("❌ Rovo CLI Timeout nach 5 Minuten")
            raise Exception("Rovo CLI Kategorisierung timeout")
        except json.JSONDecodeError as e:
            print(f"❌ Fehler beim Parsen der Rovo-Antwort: {e}")
            print(f"Rovo-Antwort war: {ai_response}")
            raise Exception(f"Rovo-Kategorisierung fehlgeschlagen: Ungültiges JSON-Format in der Antwort")
        except subprocess.CalledProcessError as e:
            print(f"❌ Rovo CLI Prozess-Fehler: {e}")
            raise Exception(f"Rovo-Kategorisierung fehlgeschlagen: CLI-Prozess-Fehler - {e}")
        except Exception as e:
            print(f"❌ Unerwarteter Fehler bei Rovo-Kategorisierung: {e}")
            raise Exception(f"Rovo-Kategorisierung fehlgeschlagen: {e}")
    
    def save_results(self, categorized_repos: Dict[str, List[Dict[str, Any]]]):
        """Speichert die kategorisierten Repositories in eine JSON-Datei"""
        output_file = 'starred_repos_categorized_rovo.json'
        
        # Bereite Ausgabeformat vor
        output_data = {
            'last_updated': f"{__import__('datetime').datetime.now().isoformat()}",
            'total_repositories': sum(len(repos) for repos in categorized_repos.values()),
            'categories': categorized_repos,
            'generated_by': 'Atlassian Rovo Dev CLI'
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(output_data, f, indent=2, ensure_ascii=False)
            
            print(f"💾 Ergebnisse gespeichert in: {output_file}")
            
            # Zeige Zusammenfassung
            print("\n📊 Kategorisierungs-Zusammenfassung:")
            for category, repos in categorized_repos.items():
                print(f"  • {category}: {len(repos)} Repositories")
                
        except Exception as e:
            print(f"❌ Fehler beim Speichern: {e}")
            raise


def main():
    try:
        print("🚀 Starte Repository-Kategorisierung mit Rovo Dev CLI...")
        categorizer = StarredRepoCategorizerRovo()
        
        # 1. Starred Repos laden
        print("\n📥 Lade starred Repositories...")
        starred_repos = categorizer.fetch_starred_repos()
        
        if not starred_repos:
            print("⚠️ Keine starred Repositories gefunden - Beende Ausführung")
            exit(0)  # Kein Fehler, einfach keine Repos
        
        # 2. Rovo-Kategorisierung
        print(f"\n🤖 Starte Rovo-Kategorisierung für {len(starred_repos)} Repositories...")
        categorized_repos = categorizer.categorize_with_rovo(starred_repos)
        
        # 3. Ergebnisse speichern
        print("\n💾 Speichere Ergebnisse...")
        categorizer.save_results(categorized_repos)
        
        print("\n🎉 Kategorisierung mit Rovo Dev CLI erfolgreich abgeschlossen!")
        
    except ValueError as e:
        print(f"\n❌ Konfigurationsfehler: {e}")
        print("💡 Überprüfe die Umgebungsvariablen (GITHUB_TOKEN, GITHUB_USERNAME, ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN)")
        exit(1)
    except Exception as e:
        print(f"\n❌ Kritischer Fehler: {e}")
        print("💡 Die GitHub Action wird mit Fehlerstatus beendet")
        exit(1)


if __name__ == "__main__":
    main()