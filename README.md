# Learning Profile

Static profile page for CTF write-ups, labs, projects, blogs and team information. Markdown articles share a generated table of contents and enhanced code blocks.

## Project structure

```text
.
|-- assets/
|   |-- css/        # Shared site styles
|   |-- images/     # Profile and team artwork
|   `-- js/         # Main page and writeup scripts
|-- data/           # Generated CTFtime data
|-- blogs/          # Blog posts and blog manifest
|-- labs/           # Hands-on labs and lab manifest
|-- projects/       # Project manifest and source examples
|-- scripts/        # Maintenance scripts
|-- writeups/       # CTF writeups grouped by event
|-- article.html    # Shared Markdown article reader
|-- index.html
```

## Edit content

- Update your name, email and links in `index.html`.
- Edit the mini CV drawer inside `<aside class="profile-card">`.
- Edit CTF content inside `[data-panel-content="ctf"]`.
- Edit tournament filter buttons with `data-event-filter`.
- Put write-up Markdown files in `writeups/`, then add one entry to `writeups/manifest.json`.
- Add project entries to `projects/manifest.json`.
- Add lab entries to `labs/manifest.json`.
- Add blog entries to `blogs/manifest.json`.
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

You do not need to create a separate HTML file or hand-write a card. `assets/js/app.js` reads `writeups/manifest.json`, renders cards, and creates tournament filters automatically.

## Add a project

Add one object to `projects/manifest.json`:

```json
{
  "type": "Security tool",
  "title": "My Tool",
  "description": "Short project description.",
  "tags": ["Python", "CLI"],
  "date": "2026-07-28",
  "src": "projects/my-tool/README.md",
  "url": "https://github.com/your-username/my-tool"
}
```

Use `src` to open project notes in the shared article reader. Leave `url` empty if the project does not have a public repository.

## Add a lab

Put the Markdown file in `labs/`, then add an entry to `labs/manifest.json`:

```json
{
  "title": "My Lab",
  "description": "Short lab summary.",
  "platform": "Hack The Box",
  "category": "Pwn",
  "difficulty": "Easy",
  "status": "Completed",
  "tags": ["Linux", "Binary"],
  "date": "2026-07-28",
  "src": "labs/my-lab/README.md"
}
```

Use `src` for lab notes in the shared article reader, or replace it with `url` to link to an external lab page.

## Add a blog

Put the Markdown file in `blogs/`, then add an entry to `blogs/manifest.json`:

```json
{
  "title": "My Blog Post",
  "description": "Short post summary.",
  "category": "Research",
  "date": "2026-07-28",
  "tags": ["Web", "Notes"],
  "src": "blogs/my-blog-post/README.md"
}
```

Headings from `#` through `####` automatically appear in the article table of contents. Fenced code blocks automatically receive a toolbar, line numbers, collapse control, and copy action.

## CTFtime achievements

Team achievements are rendered from `data/ctftime-results.json`.

The data is updated by `.github/workflows/update-ctftime-results.yml`, which runs `scripts/update_ctftime_results.py` daily and keeps only CTFtime results from 2025 and 2026 with place `<= 150`.

You can also run it manually from GitHub Actions with `workflow_dispatch`.
