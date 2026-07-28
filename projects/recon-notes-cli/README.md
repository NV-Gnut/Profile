# Recon Notes CLI

Recon Notes CLI is a small command-line workspace for keeping reconnaissance data organized during security assessments and CTF challenges.

## Overview

The project stores targets, endpoints, observations, and tested payloads in one SQLite database. The goal is to keep notes searchable without interrupting the testing workflow.

## Data model

Each workspace contains targets and their related findings.

```sql
CREATE TABLE findings (
  id INTEGER PRIMARY KEY,
  target_id INTEGER NOT NULL,
  endpoint TEXT NOT NULL,
  note TEXT NOT NULL,
  created_at TEXT NOT NULL
);
```

## Core workflow

### Create a workspace

Initialize a database for the current target.

```bash
recon-notes init example.com
recon-notes add-endpoint /api/profile
```

### Record an observation

Observations can be tagged and searched later.

```python
def add_finding(database, endpoint, note):
    database.execute(
        "INSERT INTO findings(endpoint, note) VALUES (?, ?)",
        (endpoint, note),
    )
```

## Roadmap

- Add Markdown export.
- Support reusable checklists.
- Add filtering by tag and severity.
