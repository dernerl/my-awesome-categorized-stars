# Contributing

This project automatically categorizes GitHub starred repositories using an LLM and commits the results as a Markdown report. Anyone can fork it and run their own instance.

## How It Works

A GitHub Actions workflow runs daily (05:00 UTC) or on manual trigger. It:

1. Fetches all your starred repositories via the GitHub API
2. Sends them to **Llama 3.3 70B** via [Groq](https://groq.com) for categorization
3. Commits a generated `README.md` and a JSON data file back to the repository

## Fork & Run Your Own

### 1. Fork the Repository

Click **Fork** on the top right of this page.

### 2. Get a Free Groq API Key

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up — no credit card required
3. Go to **API Keys → Create API Key**
4. Copy the key — it starts with `gsk_…`

The free tier gives you **14,400 requests/day** and is more than enough for a daily run.

### 3. Add the Secret to Your Fork

In your forked repository, go to **Settings → Secrets and variables → Actions → New repository secret**:

| Name | Value |
|------|-------|
| `GROQ_API_KEY` | your key from step 2 |

Or via CLI:

```bash
gh secret set GROQ_API_KEY --repo <your-username>/my-awesome-categorized-stars
# Paste your key when prompted
```

### 4. Enable the Workflow

GitHub disables workflows in forks by default. Go to the **Actions** tab and click **Enable workflows**.

### 5. Run It

Trigger a first run manually: **Actions → Categorize Starred Repositories (Groq / Llama) → Run workflow**.

The workflow will update `README.md` and commit `starred_repos_categorized_gemini.json` with your categorized stars.

## Project Structure

```
.
├── scripts/
│   └── categorize_starred_repos_gemini.py   # Main categorization script
├── .github/workflows/
│   └── categorize-starred-repos-gemini.yml  # Daily workflow
├── starred_repos_categorized_gemini.json    # Generated: raw data
└── README.md                                # Generated: human-readable report
```

## Customizing Categories

The LLM creates categories automatically based on your starred repos. If you want to influence the output, edit the prompt in `scripts/categorize_starred_repos_gemini.py` — look for the `prompt =` block in `categorize_with_ai()`.

The model is instructed to:
- Ignore programming language, focus on **purpose and function**
- Create **5–15 categories** in German (change the prompt language if you prefer English)
- Assign every repository to exactly one category

## Other LLM Variants (Disabled)

This repo also contains scripts for Claude (Anthropic) and OpenAI — they are disabled but available as reference in `scripts/` if you want to adapt them to a different provider.

## Requirements

No local setup needed — everything runs in GitHub Actions. The only external dependency is the Gemini API key.

## License

MIT
