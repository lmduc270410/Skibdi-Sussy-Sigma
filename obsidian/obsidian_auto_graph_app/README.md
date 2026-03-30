# Obsidian Problem Graph Generator

Local web app that:
- imports Markdown notes from your vault
- auto-analyzes each note
- builds similarity links
- exports `graph.json`
- exports `graph.canvas` for Obsidian Canvas

## Requirements

- Python 3.10+
- `Flask`
- `requests`

Optional for better analysis:
- `OPENAI_API_KEY`
- `OPENAI_MODEL` (for analysis)
- `OPENAI_EMBED_MODEL` (for embeddings, default `text-embedding-3-small`)

OpenAI API keys should stay on the server and not be put into browser code. The app is written that way.

## Install

```bash
cd obsidian_auto_graph_app
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000
```

## How to use

1. Click the folder picker and choose your vault or your `Problems/` folder.
2. Click **Analyze notes**.
3. Click **Build graph**.
4. Download `graph.json` or `graph.canvas`.
5. Put the `.canvas` file into your Obsidian vault and open it.

## Note format

Works best when your notes have frontmatter like:

```yaml
---
title: P1314
tags: [dp, prefix sums]
techniques: [prefix sums, binary search]
language: en
---
```

The app also reads:
- inline `#tags`
- `[[wikilinks]]`
- sections like `## Core Idea`, `## Solution`, `## Approach`

## What the AI does

When `OPENAI_API_KEY` is set, the server tries to:
- summarize the statement
- summarize the solution
- infer techniques
- infer the problem family
- produce a compact fingerprint
- create an embedding for better similarity search

If the API is not configured, it falls back to heuristic analysis.
