#!/usr/bin/env python3
"""
GitHub Starred Repository Categorizer mit Atlassian CLI (ACLI)
=============================================================

Dieses Script:
1. Lädt alle starred GitHub Repositories eines Benutzers
2. Verwendet die Atlassian CLI (ACLI) für KI-basierte Kategorisierung
3. Speichert die kategorisierten Ergebnisse in einer JSON-Datei

Abhängigkeiten:
- PyGithub für GitHub API
- Atlassian CLI (ACLI) installiert

Umgebungsvariablen:
- GITHUB_TOKEN: GitHub Personal Access Token
- GITHUB_USERNAME: GitHub Benutzername
- ATLASSIAN_EMAIL: Atlassian Account E-Mail
- ATLASSIAN_API_TOKEN: Atlassian API Token
- ATLASSIAN_SITE_URL: Atlassian Site URL (z.B. https://your-domain.atlassian.net)
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
        required_vars = [self.github_token, self.github_username, self.atlassian_email, self.atlassian_token]
        var_names = ['GITHUB_TOKEN', 'GITHUB_USERNAME', 'ATLASSIAN_EMAIL', 'ATLASSIAN_API_TOKEN']
        
        missing = [name for var, name in zip(required_vars, var_names) if not var]
        if missing:
            raise ValueError(f"Fehlende Umgebungsvariablen: {', '.join(missing)}")
        
        self.github = Github(self.github_token)
        
        print(f"✅ Initialisiert für GitHub: {self.github_username}")
        print(f"✅ Atlassian E-Mail: {self.atlassian_email}")
        
        # Teste ACLI Installation
        try:
            result = subprocess.run(['acli', '--version'], capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                print(f"✅ Atlassian CLI verfügbar: {result.stdout.strip()}")
            else:
                raise Exception("ACLI nicht korrekt installiert")
        except Exception as e:
            raise ValueError(f"Atlassian CLI (ACLI) nicht gefunden oder fehlerhaft: {e}")
    
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
    
    def prepare_prompt_for_acli(self, repos: List[Dict[str, Any]]) -> str:
        """Erstellt einen Prompt für die Atlassian CLI Kategorisierung"""
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
    
    def categorize_with_acli(self, repos: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Kategorisiert Repositories mit der Atlassian CLI (ACLI)"""
        if not repos:
            return {}
        
        try:
            # Erstelle Prompt
            prompt = self.prepare_prompt_for_acli(repos)
            
            print("🤖 Rufe Atlassian CLI für Kategorisierung auf...")
            
            # Erstelle temporäre Datei für den Prompt
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as temp_file:
                temp_file.write(prompt)
                temp_file_path = temp_file.name
            
            try:
                # Konfiguriere ACLI mit Credentials
                print("🔐 Konfiguriere Atlassian CLI...")
                
                # Login mit ACLI für Rovo Dev
                login_cmd = [
                    'acli', 'rovodev', 'auth', 'login',
                    '--email', self.atlassian_email,
                    '--token'
                ]
                
                # Token über stdin übertragen (sicherer)
                login_result = subprocess.run(
                    login_cmd,
                    input=self.atlassian_token,
                    text=True,
                    capture_output=True,
                    timeout=60
                )
                
                if login_result.returncode != 0:
                    print(f"⚠️ ACLI Rovo Dev Login Warnung: {login_result.stderr}")
                    # Versuche trotzdem fortzufahren
                
                # Prüfe ob Rovo Dev verfügbar ist
                rovo_help_result = subprocess.run(
                    ['acli', 'rovodev', '--help'],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if rovo_help_result.returncode == 0:
                    print("🤖 Verwende ACLI Rovo Dev für KI-Kategorisierung...")
                    
                    # Versuche interaktive Rovo Dev Session mit Prompt
                    # Da rovodev run interaktiv ist, verwenden wir eine alternative Methode
                    
                    # Verwende non-interaktiven Modus mit dem Prompt direkt
                    full_prompt = prompt + "\n\nBitte antworte nur mit JSON."
                    rovo_cmd = ['acli', 'rovodev', 'run', full_prompt]
                    
                    # Führe Rovo Dev im non-interaktiven Modus aus
                    try:
                        rovo_result = subprocess.run(
                            rovo_cmd,
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        
                        stdout = rovo_result.stdout
                        stderr = rovo_result.stderr
                        
                        if stdout:
                            print(f"🤖 Rovo Dev Antwort erhalten ({len(stdout)} Zeichen)")
                            
                            # Verbesserte JSON-Extraktion aus Rovo Dev Antwort
                            print(f"🔍 Debug: Erste 500 Zeichen der Antwort: {stdout[:500]}")
                            
                            # Mehrere Strategien für JSON-Extraktion
                            json_content = None
                            categories = None
                            
                            # Strategie 1: Suche nach kompletter JSON-Struktur
                            json_start = stdout.find('{')
                            if json_start != -1:
                                # Finde das Ende der JSON-Struktur durch Zählung der geschweiften Klammern
                                brace_count = 0
                                json_end = json_start
                                for i, char in enumerate(stdout[json_start:], json_start):
                                    if char == '{':
                                        brace_count += 1
                                    elif char == '}':
                                        brace_count -= 1
                                        if brace_count == 0:
                                            json_end = i + 1
                                            break
                                
                                if brace_count == 0:
                                    json_content = stdout[json_start:json_end]
                                    print(f"🔍 Extrahiertes JSON (Strategie 1): {json_content[:200]}...")
                                    try:
                                        categories = json.loads(json_content)
                                        print("✅ JSON erfolgreich geparst (Strategie 1)")
                                    except json.JSONDecodeError:
                                        pass
                            
                            # Strategie 2: Suche nach JSON-Code-Blöcken
                            if not categories:
                                import re
                                # Suche nach ```json ... ``` Blöcken
                                json_blocks = re.findall(r'```(?:json)?\s*(\{[^`]+\})\s*```', stdout, re.DOTALL)
                                for block in json_blocks:
                                    try:
                                        categories = json.loads(block.strip())
                                        print("✅ JSON erfolgreich geparst (Strategie 2 - Code-Block)")
                                        json_content = block.strip()
                                        break
                                    except json.JSONDecodeError:
                                        continue
                            
                            # Strategie 3: ACLI-spezifische Box-Formatierung extrahieren
                            if not categories:
                                # Entferne ACLI Box-Formatierung (│ Zeichen und Box-Ränder)
                                lines = stdout.split('\n')
                                cleaned_lines = []
                                for line in lines:
                                    # Entferne Box-Ränder und │ Präfixe
                                    line = line.strip()
                                    if line.startswith('│'):
                                        line = line[1:].strip()
                                    if line.startswith('╭') or line.startswith('╰') or line.startswith('─'):
                                        continue
                                    if line:
                                        cleaned_lines.append(line)
                                
                                cleaned_text = '\n'.join(cleaned_lines)
                                print(f"🔍 ACLI-bereinigter Text (Strategie 3): {cleaned_text[:300]}...")
                                
                                # Finde JSON in bereinigtem Text
                                json_start = cleaned_text.find('{')
                                if json_start != -1:
                                    brace_count = 0
                                    json_end = json_start
                                    for i, char in enumerate(cleaned_text[json_start:], json_start):
                                        if char == '{':
                                            brace_count += 1
                                        elif char == '}':
                                            brace_count -= 1
                                            if brace_count == 0:
                                                json_end = i + 1
                                                break
                                    
                                    if brace_count == 0:
                                        json_content = cleaned_text[json_start:json_end]
                                        print(f"🔍 Extrahiertes JSON aus ACLI (Strategie 3): {json_content[:200]}...")
                                        try:
                                            categories = json.loads(json_content)
                                            print("✅ JSON erfolgreich geparst (Strategie 3 - ACLI-bereinigt)")
                                        except json.JSONDecodeError as e:
                                            print(f"❌ JSON-Parse-Fehler (Strategie 3): {e}")
                            
                            # Strategie 4: Fallback - Entferne häufige Nicht-JSON-Präfixe und -Suffixe
                            if not categories and json_start != -1:
                                # Entferne häufige Rovo Dev Antwort-Patterns
                                cleaned = stdout
                                # Entferne Text vor dem ersten {
                                cleaned = cleaned[json_start:]
                                # Entferne Text nach dem letzten }
                                json_end = cleaned.rfind('}') + 1
                                if json_end > 0:
                                    cleaned = cleaned[:json_end]
                                    print(f"🔍 Bereinigtes JSON (Strategie 4): {cleaned[:200]}...")
                                    try:
                                        categories = json.loads(cleaned)
                                        print("✅ JSON erfolgreich geparst (Strategie 4 - Bereinigt)")
                                        json_content = cleaned
                                    except json.JSONDecodeError:
                                        pass
                            
                            if categories:
                                try:
                                    
                                    # Konvertiere zu unserem Format
                                    result_categories = {}
                                    repo_lookup = {repo['name']: repo for repo in repos}
                                    
                                    for category, repo_names in categories.items():
                                        result_categories[category] = []
                                        for repo_name in repo_names:
                                            if repo_name in repo_lookup:
                                                result_categories[category].append(repo_lookup[repo_name])
                                            else:
                                                print(f"⚠️ Repository '{repo_name}' nicht gefunden: {repo_name}")
                                    
                                    print(f"✅ Repositories in {len(result_categories)} Kategorien gruppiert")
                                    return result_categories
                                    
                                except json.JSONDecodeError:
                                    print("⚠️ Rovo Dev Antwort enthält kein gültiges JSON")
                            else:
                                print("⚠️ Keine JSON-Struktur in Rovo Dev Antwort gefunden")
                        
                        if stderr:
                            print(f"⚠️ Rovo Dev Stderr: {stderr}")
                            
                    except subprocess.TimeoutExpired:
                        print("⚠️ Rovo Dev Timeout nach 5 Minuten")
                
                # Fallback: Regelbasierte Kategorisierung
                print("ℹ️ Rovo Dev nicht verfügbar oder fehlerhaft, verwende regelbasierte Kategorisierung...")
                return self._categorize_with_rules(repos)
                
            finally:
                # Lösche temporäre Datei
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
                
        except subprocess.TimeoutExpired:
            print("❌ ACLI Timeout nach 5 Minuten")
            raise Exception("ACLI Kategorisierung timeout")
        except json.JSONDecodeError as e:
            print(f"❌ Fehler beim Parsen der ACLI-Antwort: {e}")
            print(f"ACLI-Antwort war: {ai_response if 'ai_response' in locals() else 'Nicht verfügbar'}")
            raise Exception(f"ACLI Kategorisierung fehlgeschlagen: Ungültiges JSON-Format")
        except subprocess.CalledProcessError as e:
            print(f"❌ ACLI Prozess-Fehler: {e}")
            raise Exception(f"ACLI Kategorisierung fehlgeschlagen: CLI-Prozess-Fehler - {e}")
        except Exception as e:
            print(f"❌ Unerwarteter Fehler bei ACLI Kategorisierung: {e}")
            raise Exception(f"ACLI Kategorisierung fehlgeschlagen: {e}")
    
    def _categorize_with_rules(self, repos: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """Fallback-Methode: Regelbasierte Kategorisierung"""
        print("🔄 Verwende regelbasierte Kategorisierung als Fallback...")
        
        # Für diese Demo verwenden wir eine einfache regelbasierte Kategorisierung
        # In der Praxis könnte hier eine andere AI-Integration implementiert werden
        categories = {
            "Web Development": [],
            "Mobile Development": [],
            "Data Science & ML": [],
            "DevOps & Infrastructure": [],
            "Programming Languages": [],
            "Utilities & Tools": [],
            "Other": []
        }
        
        for repo in repos:
            language = repo.get('language', '').lower() if repo.get('language') else ''
            description = repo.get('description', '').lower()
            topics = [topic.lower() for topic in repo.get('topics', [])]
            
            categorized = False
            
            # Web Development
            if any(keyword in language or keyword in description or keyword in topics 
                   for keyword in ['javascript', 'typescript', 'react', 'vue', 'angular', 'html', 'css', 'web', 'frontend', 'backend']):
                categories["Web Development"].append(repo)
                categorized = True
            
            # Mobile Development
            elif any(keyword in language or keyword in description or keyword in topics 
                     for keyword in ['swift', 'kotlin', 'flutter', 'react-native', 'ios', 'android', 'mobile']):
                categories["Mobile Development"].append(repo)
                categorized = True
            
            # Data Science & ML
            elif any(keyword in language or keyword in description or keyword in topics 
                     for keyword in ['python', 'jupyter', 'machine-learning', 'data-science', 'tensorflow', 'pytorch', 'ml', 'ai']):
                categories["Data Science & ML"].append(repo)
                categorized = True
            
            # DevOps & Infrastructure
            elif any(keyword in language or keyword in description or keyword in topics 
                     for keyword in ['docker', 'kubernetes', 'terraform', 'ansible', 'devops', 'infrastructure', 'ci-cd']):
                categories["DevOps & Infrastructure"].append(repo)
                categorized = True
            
            # Programming Languages
            elif language in ['go', 'rust', 'c++', 'c', 'java', 'scala', 'haskell', 'erlang']:
                categories["Programming Languages"].append(repo)
                categorized = True
            
            # Utilities & Tools
            elif any(keyword in description or keyword in topics 
                     for keyword in ['tool', 'utility', 'cli', 'library', 'framework']):
                categories["Utilities & Tools"].append(repo)
                categorized = True
            
            if not categorized:
                categories["Other"].append(repo)
        
        # Entferne leere Kategorien
        return {k: v for k, v in categories.items() if v}
    
    
    def save_results(self, categorized_repos: Dict[str, List[Dict[str, Any]]]):
        """Speichert die kategorisierten Repositories in eine JSON-Datei"""
        output_file = 'starred_repos_categorized_rovo.json'
        
        # Bereite Ausgabeformat vor
        output_data = {
            'last_updated': f"{__import__('datetime').datetime.now().isoformat()}",
            'total_repositories': sum(len(repos) for repos in categorized_repos.values()),
            'categories': categorized_repos,
            'generated_by': 'Atlassian CLI (ACLI)'
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
        print("🚀 Starte Repository-Kategorisierung mit Atlassian CLI...")
        categorizer = StarredRepoCategorizerRovo()
        
        # 1. Starred Repos laden
        print("\n📥 Lade starred Repositories...")
        starred_repos = categorizer.fetch_starred_repos()
        
        if not starred_repos:
            print("⚠️ Keine starred Repositories gefunden - Beende Ausführung")
            exit(0)  # Kein Fehler, einfach keine Repos
        
        # 2. ACLI Kategorisierung
        print(f"\n🤖 Starte ACLI Kategorisierung für {len(starred_repos)} Repositories...")
        categorized_repos = categorizer.categorize_with_acli(starred_repos)
        
        # 3. Ergebnisse speichern
        print("\n💾 Speichere Ergebnisse...")
        categorizer.save_results(categorized_repos)
        
        print("\n🎉 Kategorisierung mit Atlassian CLI erfolgreich abgeschlossen!")
        
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