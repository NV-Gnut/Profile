# Learning Profile

Static profile page for CTF write-ups, projects and team information. The layout uses a profile logo that opens a mini CV drawer, tab-style functions on the top right, and a write-up grid with tournament filters.

## Edit content

- Update your name, email and links in `index.html`.
- Edit the mini CV drawer inside `<aside class="profile-card">`.
- Edit CTF content inside `[data-panel-content="ctf"]`.
- Edit tournament filter buttons with `data-event-filter`.
- Put write-up Markdown files in `writeups/`, then add one entry to `writeups/manifest.json`.
- Add project entries to `projects/manifest.json`.
- Edit the team name, copy or SVG logo inside `[data-panel-content="team"]`.

## Deploy to GitHub Pages

1. Create a new GitHub repository.
2. Push this folder to the repository.
3. Open repository `Settings` -> `Pages`.
4. Under `Build and deployment`, choose `Deploy from a branch`.
5. Select branch `main` and folder `/root`, then save.

GitHub will publish the page at:

```text
https://<your-username>.github.io/<repository-name>/
```

## Add a write-up

1. Put your Markdown file anywhere inside `writeups/`, for example `writeups/My CTF/My Challenge/README.md`.
2. Add one object to `writeups/manifest.json`:

```json
{
  "title": "My Challenge",
  "event": "My CTF",
  "eventKey": "myctf",
  "category": "Web",
  "date": "2026-05-17",
  "src": "writeups/My CTF/My Challenge/README.md"
}
```

You do not need to create a separate HTML file or hand-write a card. `script.js` reads `writeups/manifest.json`, renders cards, and creates tournament filters automatically.

## Add a project

Add one object to `projects/manifest.json`:

```json
{
  "type": "Security tool",
  "title": "My Tool",
  "description": "Short project description.",
  "tags": ["Python", "CLI"],
  "url": "https://github.com/your-username/my-tool"
}
```

Leave `url` as an empty string if the project does not have a public link yet.

## CTFtime achievements

Team achievements are rendered from `data/ctftime-results.json`.

The data is updated by `.github/workflows/update-ctftime-results.yml`, which runs `scripts/update_ctftime_results.py` daily and keeps only CTFtime results from 2025 and 2026 with place `<= 150`.

You can also run it manually from GitHub Actions with `workflow_dispatch`.
