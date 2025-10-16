# 🤖 GitHub Starred Repositories Categorizer - Setup Guide

Eine GitHub Action, die automatisch Ihre gelikten (starred) Repositories mit KI kategorisiert und einen übersichtlichen Report erstellt.

## ✨ Features

- 🔄 **Automatische Kategorisierung** Ihrer starred Repositories
- 🤖 **KI-gestützte Analyse** mit OpenAI GPT-4
- 📊 **Übersichtliche Reports** in Markdown-Format
- ⏰ **Tägliche Updates** oder manuelle Ausführung
- 🏷️ **Intelligente Kategorien** basierend auf Technologie, Zweck und Domain
- 📈 **Statistiken** zu Stars, Forks und Sprachen

## 🚀 Einrichtung

### 1. Repository Setup

1. **Forken Sie dieses Repository** oder erstellen Sie ein neues
2. **Klonen Sie es lokal:**
   ```bash
   git clone https://github.com/IHR-USERNAME/starred-repos-categorizer.git
   cd starred-repos-categorizer
   ```

### 2. Secrets konfigurieren

Gehen Sie zu Ihren Repository-Einstellungen → Secrets and variables → Actions und fügen Sie hinzu:

#### Required Secrets:
- **`OPENAI_API_KEY`**: Ihr OpenAI API-Schlüssel
  - Erstellen Sie einen bei [OpenAI Platform](https://platform.openai.com/api-keys)
  - Benötigt Zugriff auf GPT-4 Modell

#### Optional (wird automatisch bereitgestellt):
- **`GITHUB_TOKEN`**: Wird automatisch von GitHub bereitgestellt

### 3. Workflow aktivieren

Die GitHub Action läuft automatisch:
- 🕐 **Täglich um 02:00 UTC**
- 🔧 **Bei manueller Auslösung** (Repository → Actions → "Categorize Starred Repositories" → "Run workflow")
- 📝 **Bei Änderungen** am Workflow-File

## 📋 Was passiert?

1. **Repositories abrufen**: Lädt alle Ihre starred Repositories
2. **KI-Analyse**: Analysiert Name, Beschreibung, Sprache und Topics
3. **Kategorisierung**: Gruppiert nach:
   - 💻 Programmiersprachen
   - 🛠️ Technologie-Stacks (Web, Mobile, AI/ML, DevOps)
   - 🎯 Zweck (Learning, Tools, Frameworks)
   - 🏗️ Domain (Frontend, Backend, Data Science)
4. **Report erstellen**: Generiert `README.md` mit kategorisierten Repositories
5. **Commit & Push**: Speichert Änderungen automatisch

## 📁 Ausgabe-Dateien

Nach der Ausführung finden Sie:

- **`README.md`**: Formatierter Markdown-Report (wird bei jedem Lauf überschrieben)
- **`starred_repos_categorized.json`**: Rohdaten im JSON-Format

## 🎯 Beispiel-Kategorien

Die KI erstellt intelligente Kategorien wie:

- **🐍 Python & Data Science**
- **⚛️ React & Frontend**
- **🔧 DevOps & Infrastructure**
- **🤖 Machine Learning & AI**
- **📱 Mobile Development**
- **🎮 Game Development**
- **📚 Learning Resources**
- **🛠️ Developer Tools**

## ⚙️ Konfiguration

### Workflow anpassen

Bearbeiten Sie `.github/workflows/categorize-starred-repos.yml`:

```yaml
on:
  schedule:
    # Ändern Sie die Zeit (aktuell 02:00 UTC täglich)
    - cron: '0 2 * * *'
```

### Script-Parameter

Das Python-Script unterstützt Umgebungsvariablen:

- `GITHUB_USERNAME`: Ihr GitHub-Benutzername (automatisch gesetzt)
- `GITHUB_TOKEN`: GitHub API Token (automatisch gesetzt)
- `OPENAI_API_KEY`: OpenAI API-Schlüssel (manuell konfigurieren)

## 🔍 Troubleshooting

### Häufige Probleme:

1. **"Keine starred Repositories gefunden"**
   - Überprüfen Sie, ob Sie öffentliche starred Repositories haben
   - GitHub Token muss Berechtigung haben, Ihre starred Repos zu lesen

2. **"OpenAI API Fehler"**
   - Überprüfen Sie Ihren API-Schlüssel
   - Stellen Sie sicher, dass Sie Guthaben/Credits haben
   - GPT-4 Zugang erforderlich

3. **"Permission denied"**
   - Repository-Einstellungen → Actions → General → Workflow permissions → "Read and write permissions"

### Logs überprüfen:

Gehen Sie zu Actions → "Categorize Starred Repositories" → Letzter Run für Details

## 📊 Kosten

- **GitHub Actions**: Kostenlos für öffentliche Repositories
- **OpenAI API**: ~$0.01-0.05 pro Durchlauf (abhängig von Anzahl der Repositories)

## 🤝 Beitragen

1. Fork des Repositories
2. Feature Branch erstellen
3. Änderungen committen
4. Pull Request erstellen

## 📄 Lizenz

MIT License - siehe [LICENSE](LICENSE) für Details