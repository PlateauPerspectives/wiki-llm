# Creating a sibling wiki on a different subject

This repo is a template as well as a wiki. A **sibling wiki** is a new repository that gets the same rules, AI workflow, Obsidian setup and navigation-tree CI, but starts with **no content** and has **its own fixed top topics**.

A script does most of the work. Plan on about 15 minutes.

---

## Step 0 — Decide your top topics (the important part)

Top topics are permanent: once there is content, they can't be renamed, merged or reordered (Rule 1 in `CLAUDE.md`). Spend the time here.

- **2–5 topics** works well. This wiki uses 3.
- Each topic needs a **folder name** (short, title case, no `/`) and optionally a longer **display title**.
  For example, folder `Creation Care` with title `Creation Care / Stewardship`.
- The folder name also gives the topic page's filename: `Creation Care` → `wiki/Creation Care/creation-care.md`.
- The order you list them in is the order they appear in the index and the navigation tree.

Also choose:

- a **wiki title**, e.g. *"Water & Land Stewardship"*
- a **repo name**, e.g. `wiki-water`
- whether a downstream app repo should be **notified** when the navigation tree changes (like `larsgson/stewardship-navTree` is for this wiki). If you're not sure, skip it — you can add it later.

---

## Step 1 — Run the scaffold script

You need Python 3.11+ (`python3 --version`). From this repo's root:

```bash
python3 scripts/new_sibling_wiki.py ../wiki-water \
  --title "Water & Land Stewardship" \
  --topic "Water Governance" \
  --topic "Soil Health=Soil Health & Regeneration" \
  --topic "Rangeland Restoration"
```

Options:

| Option | Meaning |
|---|---|
| `../wiki-water` | Where to create the new repo (must be outside this repo, and empty or not yet existing) |
| `--title` | Wiki title for the README |
| `--topic "Folder[=Title]"` | One per top topic, in order |
| `--org` | GitHub organisation/user (default `PlateauPerspectives`) |
| `--repo` | GitHub repo name (default: the folder name) |
| `--sync-repo OWNER/REPO` | Downstream repo to notify after navtree rebuilds. Omit it and that CI step is removed. |
| `--no-git` | Skip `git init` |

The script ends by building the navigation tree once, as a check. You should see one root per topic:

```
NavTree v2 output written to output/
  3 tree nodes (0 redirects), 3 unique content pieces, 3 root(s)
```

### What you get

| Copied as-is | Rewritten for your topics | Created fresh (empty) |
|---|---|---|
| `.navtree/` build script and config | `CLAUDE.md` (Rule 1, layout, examples) | `wiki/<Topic>/<topic>.md` for each topic |
| `.github/` PR template | `README.md` (title, intro, structure) | `wiki/index.md`, `log.md`, `source-registry.md` |
| `.obsidian/` settings + Homepage plugin | `ONBOARDING.md` (repo URLs) | `wiki/Sources/`, `raw/` |
| `.gitignore`, `docs/`, this script | `.github/workflows/navtree.yml` (dispatch step) | `.navtree/output/` (first build) |

Nothing from this wiki's `wiki/` or `raw/` content is copied.

---

## Step 2 — Review the generated files

Open the new folder and read, in order:

1. **`CLAUDE.md`, Rule 1.** Check that the topics are right. *Last chance to change them cheaply:* if they're wrong, delete the folder and rerun the script.
2. **`CLAUDE.md`, the rest.** The rules (copyright, source registry, private sources, page formats) are general and usually stay as they are. If your subject needs extra rules (e.g. "always record the country for each case study"), add them now.
3. **`README.md`.** Optionally rewrite the one-line description of each topic in the *Structure* block.
4. **Each `wiki/<Topic>/<topic>.md`.** These are placeholders. The first ingest will fill them in, or you can write an overview yourself.

---

## Step 3 — Put it on GitHub

1. On GitHub, create an **empty** repository (no README, no .gitignore) named as chosen, under your org.
2. In the new folder:

   ```bash
   cd ../wiki-water
   git add -A
   git commit -m "Scaffold wiki"
   git remote add origin git@github.com:PlateauPerspectives/wiki-water.git
   git push -u origin main
   ```

3. **Check that the Action is allowed to push:** repo *Settings → Actions → General → Workflow permissions* → **Read and write permissions**. (The workflow declares `contents: write`, but some org policies cap this.)
4. **If you used `--sync-repo`:** add a secret named `NAVTREE_SYNC_TOKEN` under *Settings → Secrets and variables → Actions*. It must be a GitHub token that can trigger `repository_dispatch` on the downstream repo. That repo needs a workflow listening for `navtree-updated`.
5. Invite collaborators (*Settings → Collaborators*) and point them to `ONBOARDING.md`.

To test CI: edit any `wiki/` page (e.g. bump `last_updated`), push, and watch the *Actions* tab. A green run that commits nothing is fine, since the tree hasn't changed.

---

## Step 4 — Open it and do the first ingest

1. In Obsidian: *Open folder as vault* → the new repo folder.
2. Put a first source in `raw/`, open the repo in your AI assistant, and type `ingest raw/<file>`.
3. From here on, follow [Updating the wiki](updating-the-wiki.md). It applies unchanged.

---

## Keeping siblings in sync later

Each sibling is an independent copy, so improvements made here don't flow to the others automatically. When you change shared tooling or rules (e.g. `build_navtree.py`, the generic parts of `CLAUDE.md`, `docs/`), copy them across by hand:

```bash
# from this repo, into a sibling
cp .navtree/build_navtree.py ../wiki-water/.navtree/
cp docs/updating-the-wiki.md ../wiki-water/docs/
```

Don't copy `CLAUDE.md` wholesale, because each sibling has its own Rule 1. Copy the changed sections instead, or ask the AI: *"apply the rule changes from ../wiki-llm/CLAUDE.md to this CLAUDE.md, keeping our topics."*

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Template drift: could not find …` | `CLAUDE.md` or `README.md` in the template repo changed shape, and the script couldn't find what it rewrites. Update the matching pattern in `scripts/new_sibling_wiki.py`, or fix the generated file by hand. |
| `already exists and is not empty` | Choose a new folder, or delete the old attempt. |
| The build shows 0 roots | `wiki/index.md` must have a non-indented `- [[Topic/topic]]` bullet under each topic's `##` heading. |
| The CI push fails with 403 | Set workflow permissions to read and write (Step 3.3). |
| The dispatch step fails | `NAVTREE_SYNC_TOKEN` is missing or lacks access to the downstream repo. Remove the step if you don't need it. |
