# 🔧 Troubleshooting Guide

## 🚨 Häufige Probleme und Lösungen

### 1. "Fehlende Umgebungsvariable: OPENAI_API_KEY"

**Problem:** Der OpenAI API-Schlüssel ist nicht konfiguriert.

**Lösung:**
1. Gehen Sie zu Repository → Settings → Secrets and variables → Actions
2. Erstellen Sie ein neues Secret mit dem Namen `OPENAI_API_KEY` (genau so geschrieben)
3. Fügen Sie Ihren OpenAI API-Schlüssel ein

### 2. "Permission denied" beim Push

**Problem:** GitHub Action hat keine Schreibberechtigung.

**Lösung:**
1. Repository → Settings → Actions → General
2. Unter "Workflow permissions" wählen Sie "Read and write permissions"
3. Speichern Sie die Einstellungen

### 3. "No starred repositories found"

**Problem:** Keine öffentlichen starred Repositories gefunden.

**Mögliche Ursachen:**
- Ihr Profil ist privat
- Sie haben keine öffentlichen starred Repositories
- GitHub Token hat keine Berechtigung

**Lösung:**
- Überprüfen Sie Ihre GitHub-Profileinstellungen
- Stellen Sie sicher, dass starred Repositories öffentlich sichtbar sind

### 4. OpenAI API Rate Limits

**Problem:** Zu viele API-Aufrufe in kurzer Zeit.

**Symptome:**
```
RateLimitError: You exceeded your current quota
```

**Lösung:**
- Überprüfen Sie Ihr OpenAI-Guthaben
- Reduzieren Sie die Anzahl der Repositories (Filter hinzufügen)
- Erhöhen Sie das Intervall zwischen den Läufen

### 5. GitHub API Rate Limits

**Problem:** Zu viele GitHub API-Aufrufe.

**Symptome:**
```
RateLimitExceeded: API rate limit exceeded
```

**Lösung:**
- Warten Sie bis zur nächsten Rate-Limit-Zurücksetzung
- Verwenden Sie ein Personal Access Token mit höheren Limits

## 🔍 Debug-Tipps

### Logs analysieren

1. Gehen Sie zu Actions → "Categorize Starred Repositories"
2. Klicken Sie auf den letzten Lauf
3. Erweitern Sie die Schritte für Details

### Lokales Testen

```bash
# Umgebungsvariablen setzen
export GITHUB_TOKEN="your_token"
export OPENAI_API_KEY="your_key"
export GITHUB_USERNAME="your_username"

# Script lokal ausführen
python scripts/categorize_starred_repos.py
```

### Debug-Modus aktivieren

Fügen Sie temporär Debug-Ausgaben hinzu:

```python
# In categorize_starred_repos.py
print(f"Verarbeite {len(repos)} Repositories...")
print(f"Erste 5 Repos: {[r['name'] for r in repos[:5]]}")
```

## 📞 Support

Bei weiteren Problemen:

1. **Erstellen Sie ein Issue** mit:
   - Fehlermeldung (vollständig)
   - GitHub Actions Logs
   - Ihre Konfiguration (ohne Secrets!)

2. **Überprüfen Sie bestehende Issues** für ähnliche Probleme

3. **Community-Support** im Discussions-Bereich